"""
API Views for Dashboard App

This module contains all REST API views for the LLM Observability Dashboard.
Includes views for traces, analytics, and configuration.
"""

import csv
import logging
from datetime import timedelta
from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q

from rest_framework import status, generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import LLMTrace, APIConfiguration
from .serializers import (
    LLMTraceSerializer,
    LLMTraceCreateSerializer,
    LLMTraceListSerializer,
    APIConfigurationSerializer,
    APIKeyUpdateSerializer,
    TestLLMSerializer,
    AnalyticsOverviewSerializer,
    ChartDataSerializer,
)
from .utils import (
    call_groq_llm,
    get_dashboard_overview,
    get_chart_data,
    get_available_models,
    test_api_connection,
    calculate_cost,
)

logger = logging.getLogger('dashboard')


class StandardPagination(PageNumberPagination):
    """Standard pagination for list views."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class LLMTraceListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating LLM traces.
    
    GET: List all traces with pagination and filtering
    POST: Create a new trace record
    
    RBAC: Superusers see all traces, regular users see only their own.
    """
    
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['prompt', 'response', 'model_name']
    ordering_fields = ['timestamp', 'latency_ms', 'total_tokens', 'cost_usd', 'status']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """Use different serializers for list vs create."""
        if self.request.method == 'POST':
            return LLMTraceCreateSerializer
        return LLMTraceListSerializer
    
    def get_queryset(self):
        """Apply RBAC filtering and additional filters from query parameters."""
        # RBAC: Superusers see all, regular users see only their own data
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            queryset = LLMTrace.objects.all().order_by('-timestamp')
        elif user.is_authenticated:
            queryset = LLMTrace.objects.filter(user=user).order_by('-timestamp')
        else:
            queryset = LLMTrace.objects.none()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter in ['success', 'error']:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by model
        model_filter = self.request.query_params.get('model')
        if model_filter:
            queryset = queryset.filter(model_name__icontains=model_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new trace with validation."""
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            trace = serializer.save()
            
            # Return full trace data
            response_serializer = LLMTraceSerializer(trace)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating trace: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LLMTraceDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single trace detail.
    
    GET: Get full details of a specific trace
    
    RBAC: Superusers can view all traces, regular users only their own.
    """
    
    serializer_class = LLMTraceSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Apply RBAC filtering."""
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            return LLMTrace.objects.all()
        elif user.is_authenticated:
            return LLMTrace.objects.filter(user=user)
        return LLMTrace.objects.none()


class AnalyticsOverviewView(APIView):
    """
    API endpoint for dashboard analytics overview.
    
    GET: Return comprehensive summary statistics
    
    RBAC: Superusers see all stats, regular users see only their own.
    """
    
    def get(self, request):
        """Get dashboard overview statistics."""
        try:
            user = request.user if request.user.is_authenticated else None
            data = get_dashboard_overview(user=user)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting analytics overview: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsChartsView(APIView):
    """
    API endpoint for chart data.
    
    GET: Return data formatted for various charts
    
    RBAC: Superusers see all chart data, regular users see only their own.
    """
    
    def get(self, request):
        """Get chart data for the dashboard."""
        try:
            # Get days parameter (default 7)
            days = int(request.query_params.get('days', 7))
            days = min(max(days, 1), 90)  # Limit between 1 and 90 days
            
            user = request.user if request.user.is_authenticated else None
            data = get_chart_data(days, user=user)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting chart data: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class APIConfigurationView(APIView):
    """
    API endpoint for API configuration.
    
    GET: Check if API key is configured (doesn't return actual key)
    POST: Save a new API key
    """
    
    def get(self, request):
        """Check API key configuration status."""
        try:
            config = APIConfiguration.load()
            serializer = APIConfigurationSerializer(config)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting API configuration: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Save API key."""
        try:
            serializer = APIKeyUpdateSerializer(data=request.data)
            
            if serializer.is_valid():
                config = serializer.save()
                
                return Response({
                    'success': True,
                    'message': 'API key saved successfully',
                    'is_active': config.is_active,
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error saving API key: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestConnectionView(APIView):
    """
    API endpoint for testing the Groq API connection.
    
    POST: Test the API connection with a simple request
    """
    
    def post(self, request):
        """Test API connection."""
        try:
            success, message = test_api_connection()
            
            return Response({
                'success': success,
                'message': message,
            }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestLLMView(APIView):
    """
    API endpoint for testing LLM calls.
    
    POST: Make a test LLM call and auto-log it
    """
    
    def post(self, request):
        """Make a test LLM call."""
        serializer = TestLLMSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Extract validated data
            prompt = serializer.validated_data['prompt']
            model = serializer.validated_data.get('model')
            
            # Get user if authenticated
            user = request.user if request.user.is_authenticated else None
            
            # Make the LLM call
            result = call_groq_llm(
                prompt=prompt,
                model_name=model,
                auto_log=True,
                user=user
            )
            
            # Convert Decimal to float for JSON serialization
            result['cost_usd'] = float(result['cost_usd'])
            
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in test LLM call: {str(e)}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AvailableModelsView(APIView):
    """
    API endpoint for getting available LLM models.
    
    GET: Return list of available models with descriptions
    """
    
    def get(self, request):
        """Get list of available models."""
        try:
            models = get_available_models()
            return Response({'models': models}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateDefaultModelView(APIView):
    """
    API endpoint for updating the default model.
    
    POST: Update the default LLM model
    """
    
    def post(self, request):
        """Update default model."""
        try:
            model_name = request.data.get('model')
            
            if not model_name:
                return Response(
                    {'error': 'Model name is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            config = APIConfiguration.load()
            config.default_model = model_name
            config.save()
            
            return Response({
                'success': True,
                'message': f'Default model updated to {model_name}',
                'default_model': model_name,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating default model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExportTracesView(APIView):
    """
    API endpoint for exporting traces to CSV.
    
    GET: Export traces based on filters
    
    RBAC: Superusers export all traces, regular users export only their own.
    """
    
    def get(self, request):
        """Export traces to CSV."""
        try:
            # RBAC: Superusers see all, regular users see only their own data
            user = request.user
            if user.is_authenticated and user.is_superuser:
                queryset = LLMTrace.objects.all().order_by('-timestamp')
            elif user.is_authenticated:
                queryset = LLMTrace.objects.filter(user=user).order_by('-timestamp')
            else:
                queryset = LLMTrace.objects.none()
            
            # Apply filters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            status_filter = request.query_params.get('status')
            model_filter = request.query_params.get('model')
            
            if start_date:
                queryset = queryset.filter(timestamp__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(timestamp__date__lte=end_date)
            if status_filter and status_filter != 'all':
                queryset = queryset.filter(status=status_filter)
            if model_filter:
                queryset = queryset.filter(model_name__icontains=model_filter)
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="llm_traces.csv"'
            
            writer = csv.writer(response)
            
            # Write header
            writer.writerow([
                'ID',
                'Timestamp',
                'Model',
                'Status',
                'Input Tokens',
                'Output Tokens',
                'Total Tokens',
                'Latency (ms)',
                'Cost (USD)',
                'Prompt',
                'Response',
                'Error Message',
            ])
            
            # Write data rows
            for trace in queryset[:10000]:  # Limit to 10000 rows
                writer.writerow([
                    trace.id,
                    trace.timestamp.isoformat(),
                    trace.model_name,
                    trace.status,
                    trace.input_tokens,
                    trace.output_tokens,
                    trace.total_tokens,
                    trace.latency_ms,
                    trace.cost_usd,
                    trace.prompt[:500] if trace.prompt else '',  # Truncate for CSV
                    trace.response[:500] if trace.response else '',
                    trace.error_message or '',
                ])
            
            return response
        except Exception as e:
            logger.error(f"Error exporting traces: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecentTracesView(APIView):
    """
    API endpoint for getting recent traces (for dashboard widget).
    
    GET: Return the most recent traces
    
    RBAC: Superusers see all recent traces, regular users see only their own.
    """
    
    def get(self, request):
        """Get recent traces."""
        try:
            limit = int(request.query_params.get('limit', 10))
            limit = min(max(limit, 1), 50)  # Limit between 1 and 50
            
            # RBAC: Superusers see all, regular users see only their own data
            user = request.user
            if user.is_authenticated and user.is_superuser:
                traces = LLMTrace.objects.all().order_by('-timestamp')[:limit]
            elif user.is_authenticated:
                traces = LLMTrace.objects.filter(user=user).order_by('-timestamp')[:limit]
            else:
                traces = LLMTrace.objects.none()
            
            serializer = LLMTraceListSerializer(traces, many=True)
            
            return Response({
                'count': len(serializer.data),
                'traces': serializer.data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting recent traces: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchTracesView(APIView):
    """
    API endpoint for searching traces.
    
    GET: Search traces by prompt/response content
    
    RBAC: Superusers search all traces, regular users search only their own.
    """
    
    def get(self, request):
        """Search traces."""
        try:
            query = request.query_params.get('q', '')
            limit = int(request.query_params.get('limit', 25))
            limit = min(max(limit, 1), 100)
            
            if not query:
                return Response({
                    'count': 0,
                    'traces': [],
                }, status=status.HTTP_200_OK)
            
            # RBAC: Superusers see all, regular users see only their own data
            user = request.user
            if user.is_authenticated and user.is_superuser:
                base_queryset = LLMTrace.objects.all()
            elif user.is_authenticated:
                base_queryset = LLMTrace.objects.filter(user=user)
            else:
                base_queryset = LLMTrace.objects.none()
            
            # Search in prompt, response, model_name
            traces = base_queryset.filter(
                Q(prompt__icontains=query) |
                Q(response__icontains=query) |
                Q(model_name__icontains=query)
            ).order_by('-timestamp')[:limit]
            
            serializer = LLMTraceListSerializer(traces, many=True)
            
            return Response({
                'count': len(serializer.data),
                'query': query,
                'traces': serializer.data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error searching traces: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearDataView(APIView):
    """
    API endpoint for clearing traces and analytics data.
    
    POST: Delete LLM traces from the database
    
    RBAC: Superusers can clear all data, regular users can only clear their own data.
    """
    
    def post(self, request):
        """Clear data from the database."""
        try:
            # RBAC: Superusers can clear all, regular users clear only their own data
            user = request.user
            if user.is_authenticated and user.is_superuser:
                count, _ = LLMTrace.objects.all().delete()
                message = f'Deleted {count} traces (all data)'
            elif user.is_authenticated:
                count, _ = LLMTrace.objects.filter(user=user).delete()
                message = f'Deleted {count} traces (your data only)'
            else:
                return Response({
                    'success': False,
                    'error': 'Authentication required',
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Invalidate caches
            from .utils import invalidate_dashboard_cache
            invalidate_dashboard_cache()
            
            logger.info(f"Cleared data: {message}")
            
            return Response({
                'success': True,
                'message': message,
                'deleted_count': count,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserFeedbackCreateView(APIView):
    """
    API endpoint for creating user feedback on LLM responses.
    
    POST: Submit feedback for a specific trace
    """
    
    def post(self, request):
        """Create feedback for a trace."""
        from .serializers import UserFeedbackCreateSerializer
        from .models import UserFeedback
        
        serializer = UserFeedbackCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            feedback = serializer.save()
            return Response({
                'success': True,
                'feedback_id': feedback.id,
                'message': 'Feedback submitted successfully'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating feedback: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserFeedbackListView(APIView):
    """
    API endpoint for listing feedback for a trace.
    
    GET: Get all feedback for a specific trace
    """
    
    def get(self, request, trace_id):
        """Get feedback for a trace."""
        from .serializers import UserFeedbackSerializer
        from .models import UserFeedback
        
        try:
            feedback = UserFeedback.objects.filter(trace_id=trace_id).order_by('-created_at')
            serializer = UserFeedbackSerializer(feedback, many=True)
            return Response({
                'trace_id': trace_id,
                'count': len(serializer.data),
                'feedback': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching feedback: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
