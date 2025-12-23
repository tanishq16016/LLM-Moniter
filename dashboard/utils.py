"""
Utility Functions for Dashboard App

This module contains all utility functions including:
- Groq API integration
- Cost calculation
- Token counting
- Redis caching utilities
"""

import time
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from groq import Groq

from .models import APIConfiguration, LLMTrace

logger = logging.getLogger('dashboard')


# LLM Pricing per 1 million tokens (from settings)
LLM_PRICING = getattr(settings, 'LLM_PRICING', {
    'llama-3.1-8b-instant': {'input': 0.05, 'output': 0.08},
})

# Default model (fallback if not configured)
DEFAULT_MODEL = getattr(settings, 'DEFAULT_LLM_MODEL', 'llama-3.1-8b-instant')

# Cache timeout (30 seconds for real-time stats)
CACHE_TTL = getattr(settings, 'CACHE_TTL', 30)


def get_groq_client() -> Optional[Groq]:
    """
    Get a configured Groq client using the stored API key.
    
    Returns:
        Groq: Configured Groq client instance, or None if not configured
    """
    try:
        config = APIConfiguration.load()
        api_key = config.get_api_key()
        
        if not api_key:
            logger.warning("Groq API key not configured")
            return None
        
        return Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to create Groq client: {str(e)}")
        return None


def calculate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int
) -> Decimal:
    """
    Calculate the cost of an LLM call based on tokens and model.
    
    Args:
        model_name: Name of the LLM model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Decimal: Calculated cost in USD
    """
    # Get pricing for the model, default to most expensive if unknown
    pricing = LLM_PRICING.get(model_name, {'input': 0.79, 'output': 0.79})
    
    # Calculate cost (pricing is per 1 million tokens)
    input_cost = Decimal(str(input_tokens)) * Decimal(str(pricing['input'])) / Decimal('1000000')
    output_cost = Decimal(str(output_tokens)) * Decimal(str(pricing['output'])) / Decimal('1000000')
    
    total_cost = input_cost + output_cost
    
    return total_cost.quantize(Decimal('0.000001'))


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    Uses a rough approximation of ~4 characters per token for English text.
    
    Args:
        text: Input text to estimate tokens for
    
    Returns:
        int: Estimated token count
    """
    if not text:
        return 0
    
    # Rough estimation: ~4 characters per token on average
    # This is a simplified estimation; actual tokenization varies by model
    char_count = len(text)
    word_count = len(text.split())
    
    # Use average of character-based and word-based estimation
    char_estimate = char_count / 4
    word_estimate = word_count * 1.3  # ~1.3 tokens per word
    
    return int((char_estimate + word_estimate) / 2)


def call_groq_llm(
    prompt: str,
    model_name: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    auto_log: bool = True,
    user = None
) -> Dict[str, Any]:
    """
    Make a call to the Groq LLM API and optionally log the trace.
    
    Args:
        prompt: The user prompt to send
        model_name: Model to use (uses default if not specified)
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens in response
        temperature: Response temperature (creativity)
        auto_log: Whether to automatically log the trace
        user: User making the request
    
    Returns:
        Dict containing:
            - success: bool indicating if call was successful
            - response: The LLM response text
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - total_tokens: Total token count
            - latency_ms: Response time in milliseconds
            - cost_usd: Calculated cost
            - model: Model used
            - error: Error message if failed
            - trace_id: ID of the logged trace (if auto_log=True)
            - request_id: Request ID from Groq API
    """
    # Get model name
    if not model_name:
        config = APIConfiguration.load()
        model_name = config.default_model or DEFAULT_MODEL
    
    # Initialize result dictionary
    result = {
        'success': False,
        'response': '',
        'input_tokens': 0,
        'output_tokens': 0,
        'total_tokens': 0,
        'latency_ms': 0,
        'cost_usd': Decimal('0'),
        'model': model_name,
        'error': None,
        'trace_id': None,
        'request_id': None,
    }
    
    # Get Groq client
    client = get_groq_client()
    if not client:
        result['error'] = "Groq API key not configured. Please configure in Settings."
        if auto_log:
            trace = log_trace(
                model_name=model_name,
                prompt=prompt,
                response='',
                input_tokens=estimate_tokens(prompt),
                output_tokens=0,
                latency_ms=0,
                status='error',
                error_message=result['error'],
                user=user
            )
            result['trace_id'] = trace.id
        return result
    
    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Make the API call with timing
    start_time = time.perf_counter()
    
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        # Extract response data
        response_text = completion.choices[0].message.content
        usage = completion.usage
        
        result['success'] = True
        result['response'] = response_text
        result['input_tokens'] = usage.prompt_tokens
        result['output_tokens'] = usage.completion_tokens
        result['total_tokens'] = usage.total_tokens
        result['latency_ms'] = round(latency_ms, 2)
        result['cost_usd'] = calculate_cost(
            model_name,
            usage.prompt_tokens,
            usage.completion_tokens
        )
        result['request_id'] = completion.id if hasattr(completion, 'id') else None
        
        # Log the trace
        if auto_log:
            trace = log_trace(
                model_name=model_name,
                prompt=prompt,
                response=response_text,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                latency_ms=latency_ms,
                status='success',
                cost_usd=result['cost_usd'],
                request_id=result['request_id'],
                user=user
            )
            result['trace_id'] = trace.id
        
        logger.info(
            f"LLM call successful: model={model_name}, "
            f"tokens={result['total_tokens']}, latency={latency_ms:.0f}ms"
        )
        
    except Exception as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        error_message = str(e)
        result['error'] = error_message
        result['latency_ms'] = round(latency_ms, 2)
        
        # Estimate tokens for error case
        result['input_tokens'] = estimate_tokens(prompt)
        
        # Log the error trace
        if auto_log:
            trace = log_trace(
                model_name=model_name,
                prompt=prompt,
                response='',
                input_tokens=result['input_tokens'],
                output_tokens=0,
                latency_ms=latency_ms,
                status='error',
                error_message=error_message,
                user=user
            )
            result['trace_id'] = trace.id
        
        logger.error(f"LLM call failed: {error_message}")
    
    return result


def log_trace(
    model_name: str,
    prompt: str,
    response: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    status: str = 'success',
    error_message: Optional[str] = None,
    cost_usd: Optional[Decimal] = None,
    request_id: Optional[str] = None,
    user = None
) -> LLMTrace:
    """
    Log an LLM trace to the database.
    
    Args:
        model_name: Name of the model used
        prompt: Input prompt
        response: LLM response
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        latency_ms: Response latency in milliseconds
        status: 'success' or 'error'
        error_message: Error message if status is 'error'
        cost_usd: Pre-calculated cost (will be calculated if None)
        request_id: Request ID from the API
        user: User who made the request
    
    Returns:
        LLMTrace: The created trace instance
    """
    # Calculate cost if not provided
    if cost_usd is None:
        cost_usd = calculate_cost(model_name, input_tokens, output_tokens)
    
    # Create and save trace
    trace = LLMTrace.objects.create(
        timestamp=timezone.now(),
        model_name=model_name,
        prompt=prompt,
        response=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        status=status,
        error_message=error_message,
        request_id=request_id,
        user=user
    )
    
    # Invalidate relevant caches
    invalidate_dashboard_cache()
    
    return trace


def invalidate_dashboard_cache():
    """
    Invalidate all dashboard-related cache entries.
    """
    cache_keys = [
        'dashboard_overview',
        'dashboard_charts',
        'recent_traces',
        'model_stats',
        'error_rate',
    ]
    for key in cache_keys:
        cache.delete(key)


def get_cached_overview() -> Optional[Dict[str, Any]]:
    """
    Get cached dashboard overview data.
    
    Returns:
        Dict: Cached overview data or None if not cached
    """
    try:
        return cache.get('dashboard_overview')
    except Exception:
        return None


def set_cached_overview(data: Dict[str, Any]):
    """
    Cache dashboard overview data.
    
    Args:
        data: Overview data to cache
    """
    try:
        cache.set('dashboard_overview', data, CACHE_TTL)
    except Exception:
        pass  # Silently fail if Redis is unavailable


def get_cached_charts() -> Optional[Dict[str, Any]]:
    """
    Get cached chart data.
    
    Returns:
        Dict: Cached chart data or None if not cached
    """
    try:
        return cache.get('dashboard_charts')
    except Exception:
        return None


def set_cached_charts(data: Dict[str, Any]):
    """
    Cache chart data.
    
    Args:
        data: Chart data to cache
    """
    try:
        cache.set('dashboard_charts', data, CACHE_TTL)
    except Exception:
        pass  # Silently fail if Redis is unavailable


def get_dashboard_overview(user=None) -> Dict[str, Any]:
    """
    Get comprehensive dashboard overview statistics.
    Uses caching for performance.
    
    Args:
        user: The user making the request. If superuser, shows all data.
              Regular users only see their own data.
    
    Returns:
        Dict: Dashboard overview data including:
            - Request counts (today/week/month/all)
            - Average latency
            - Token totals
            - Cost totals
            - Error rates
            - Top models/users/features
    """
    # Note: Caching is disabled for RBAC as each user sees different data
    # For performance optimization, consider user-specific cache keys
    
    # Calculate date ranges
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    # Get base queryset with RBAC filtering
    if user and user.is_authenticated:
        if user.is_superuser:
            traces = LLMTrace.objects.all()
        else:
            traces = LLMTrace.objects.filter(user=user)
    else:
        traces = LLMTrace.objects.none()
    
    # Count queries
    total_all = traces.count()
    total_today = traces.filter(timestamp__gte=today_start).count()
    total_week = traces.filter(timestamp__gte=week_start).count()
    total_month = traces.filter(timestamp__gte=month_start).count()
    
    # Status counts
    success_count = traces.filter(status='success').count()
    error_count = traces.filter(status='error').count()
    
    # Error rate calculation
    error_rate = (error_count / total_all * 100) if total_all > 0 else 0
    
    # Aggregate metrics
    from django.db.models import Sum, Avg
    
    aggregates = traces.aggregate(
        total_tokens=Sum('total_tokens'),
        total_input_tokens=Sum('input_tokens'),
        total_output_tokens=Sum('output_tokens'),
        total_cost=Sum('cost_usd'),
        avg_latency=Avg('latency_ms')
    )
    
    # Top models
    from django.db.models import Count
    top_models = list(
        traces.values('model_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    
    # Build response
    data = {
        'total_requests_today': total_today,
        'total_requests_week': total_week,
        'total_requests_month': total_month,
        'total_requests_all': total_all,
        'average_latency_ms': round(aggregates['avg_latency'] or 0, 2),
        'total_tokens': aggregates['total_tokens'] or 0,
        'total_input_tokens': aggregates['total_input_tokens'] or 0,
        'total_output_tokens': aggregates['total_output_tokens'] or 0,
        'total_cost_usd': float(aggregates['total_cost'] or 0),
        'error_rate_percent': round(error_rate, 2),
        'success_count': success_count,
        'error_count': error_count,
        'top_models': top_models,
    }
    
    return data


def get_chart_data(days: int = 7, user=None) -> Dict[str, Any]:
    """
    Get data for dashboard charts.
    
    Args:
        days: Number of days to include in the data
        user: The user making the request. If superuser, shows all data.
              Regular users only see their own data.
    
    Returns:
        Dict: Chart data for various visualizations
    """
    # Note: Caching is disabled for RBAC as each user sees different data
    
    from django.db.models import Sum, Avg, Count
    from django.db.models.functions import TruncHour, TruncDate
    
    # Calculate date range
    now = timezone.now()
    start_date = now - timedelta(days=days)
    
    # Get traces in range with RBAC filtering
    if user and user.is_authenticated:
        if user.is_superuser:
            traces = LLMTrace.objects.filter(timestamp__gte=start_date)
        else:
            traces = LLMTrace.objects.filter(timestamp__gte=start_date, user=user)
    else:
        traces = LLMTrace.objects.none()
    
    # Tokens over time (hourly for last 24 hours, daily for longer)
    if days <= 1:
        tokens_over_time = list(
            traces.annotate(period=TruncHour('timestamp'))
            .values('period')
            .annotate(
                total_tokens=Sum('total_tokens'),
                input_tokens=Sum('input_tokens'),
                output_tokens=Sum('output_tokens'),
                requests=Count('id')
            )
            .order_by('period')
        )
    else:
        tokens_over_time = list(
            traces.annotate(period=TruncDate('timestamp'))
            .values('period')
            .annotate(
                total_tokens=Sum('total_tokens'),
                input_tokens=Sum('input_tokens'),
                output_tokens=Sum('output_tokens'),
                requests=Count('id')
            )
            .order_by('period')
        )
    
    # Format dates for JSON
    for item in tokens_over_time:
        item['period'] = item['period'].isoformat() if item['period'] else None
    
    # Latency trends
    latency_trends = list(
        traces.annotate(period=TruncHour('timestamp') if days <= 1 else TruncDate('timestamp'))
        .values('period')
        .annotate(avg_latency=Avg('latency_ms'))
        .order_by('period')
    )
    
    for item in latency_trends:
        item['period'] = item['period'].isoformat() if item['period'] else None
        item['avg_latency'] = round(item['avg_latency'] or 0, 2)
    
    # Error rate over time
    error_rate_data = list(
        traces.annotate(period=TruncHour('timestamp') if days <= 1 else TruncDate('timestamp'))
        .values('period')
        .annotate(
            total=Count('id'),
            errors=Count('id', filter=models.Q(status='error'))
        )
        .order_by('period')
    )
    
    error_rate_over_time = []
    for item in error_rate_data:
        rate = (item['errors'] / item['total'] * 100) if item['total'] > 0 else 0
        error_rate_over_time.append({
            'period': item['period'].isoformat() if item['period'] else None,
            'error_rate': round(rate, 2),
            'total': item['total'],
            'errors': item['errors']
        })
    
    # Cost by model
    cost_by_model = list(
        traces.values('model_name')
        .annotate(
            total_cost=Sum('cost_usd'),
            total_tokens=Sum('total_tokens'),
            requests=Count('id')
        )
        .order_by('-total_cost')
    )
    
    for item in cost_by_model:
        item['total_cost'] = float(item['total_cost'] or 0)
    
    # Requests by model (for pie chart)
    requests_by_model = list(
        traces.values('model_name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Requests by hour of day (for heatmap)
    from django.db.models.functions import ExtractHour
    requests_by_hour = list(
        traces.annotate(hour=ExtractHour('timestamp'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    
    # Build response
    data = {
        'tokens_over_time': tokens_over_time,
        'latency_trends': latency_trends,
        'error_rate_over_time': error_rate_over_time,
        'cost_by_model': cost_by_model,
        'requests_by_model': requests_by_model,
        'requests_by_hour': requests_by_hour,
    }
    
    return data


def get_available_models() -> list:
    """
    Get list of available LLM models with their descriptions.
    
    Returns:
        list: List of model dictionaries with name, description, and pricing
    """
    models = []
    for model_name, info in LLM_PRICING.items():
        models.append({
            'name': model_name,
            'description': info.get('description', ''),
            'input_price': info['input'],
            'output_price': info['output'],
        })
    return models


def test_api_connection() -> Tuple[bool, str]:
    """
    Test the Groq API connection with a simple request.
    Uses the configured default model.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    client = get_groq_client()
    if not client:
        return False, "API key not configured"
    
    # Get default model from configuration
    config = APIConfiguration.load()
    test_model = config.default_model or DEFAULT_MODEL
    
    try:
        completion = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Say 'API connection successful!' in exactly those words."}],
            max_tokens=20,
            temperature=0,
        )
        
        response = completion.choices[0].message.content
        return True, f"Connection successful with {test_model}! Response: {response}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


# Import models for QuerySet operations
from django.db import models
