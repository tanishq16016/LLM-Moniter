"""
Dashboard Models

This module contains all database models for the LLM Observability Dashboard:
- LLMTrace: Stores individual LLM API call records with metrics
- APIConfiguration: Singleton model for storing API configuration
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import User
import base64


class APIConfiguration(models.Model):
    """
    Singleton model for storing API configuration.
    Uses encrypted storage for sensitive API keys.
    """
    
    groq_api_key_encrypted = models.TextField(
        blank=True,
        default='',
        help_text='Encrypted Groq API key'
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Whether the API configuration is active'
    )
    default_model = models.CharField(
        max_length=100,
        default='llama-3.1-8b-instant',
        help_text='Default LLM model to use'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Creation timestamp'
    )
    
    class Meta:
        verbose_name = 'API Configuration'
        verbose_name_plural = 'API Configuration'
    
    def __str__(self):
        status = 'Active' if self.is_active else 'Inactive'
        return f'API Configuration ({status})'
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure only one instance exists (singleton pattern).
        """
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Prevent deletion of the singleton instance.
        """
        pass
    
    @classmethod
    def load(cls):
        """
        Load the singleton instance, creating it if it doesn't exist.
        
        Returns:
            APIConfiguration: The singleton configuration instance
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def _get_fernet(self):
        """
        Get Fernet encryption instance.
        
        Returns:
            Fernet: Fernet encryption instance
        """
        key = settings.ENCRYPTION_KEY
        if not key:
            # Generate a default key if not configured (development only)
            key = Fernet.generate_key().decode()
        # Ensure key is properly formatted
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)
    
    def set_api_key(self, api_key):
        """
        Encrypt and store the API key.
        
        Args:
            api_key (str): Plain text API key to encrypt and store
        """
        if api_key:
            fernet = self._get_fernet()
            encrypted = fernet.encrypt(api_key.encode())
            self.groq_api_key_encrypted = base64.b64encode(encrypted).decode()
            self.is_active = True
        else:
            self.groq_api_key_encrypted = ''
            self.is_active = False
    
    def get_api_key(self):
        """
        Decrypt and return the API key.
        
        Returns:
            str: Decrypted API key or empty string if not set
        """
        if self.groq_api_key_encrypted:
            try:
                fernet = self._get_fernet()
                encrypted = base64.b64decode(self.groq_api_key_encrypted.encode())
                return fernet.decrypt(encrypted).decode()
            except Exception:
                return ''
        return ''
    
    def has_api_key(self):
        """
        Check if an API key is configured.
        
        Returns:
            bool: True if API key is configured
        """
        return bool(self.groq_api_key_encrypted) and self.is_active


class LLMTrace(models.Model):
    """
    Model to store LLM API call traces with comprehensive metrics.
    Each record represents a single LLM API call with all associated data.
    """
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    
    # Timestamps
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When the LLM call was made'
    )
    
    # Model Information
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Name of the LLM model used (e.g., llama-3.1-70b)'
    )
    
    # Request/Response Data
    prompt = models.TextField(
        help_text='The input prompt sent to the LLM'
    )
    response = models.TextField(
        blank=True,
        default='',
        help_text='The response received from the LLM'
    )
    
    # Token Metrics
    input_tokens = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Number of input tokens'
    )
    output_tokens = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Number of output tokens'
    )
    total_tokens = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Total tokens (input + output)'
    )
    
    # Performance Metrics
    latency_ms = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0)],
        help_text='Response time in milliseconds'
    )
    
    # Cost Tracking
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0.0,
        validators=[MinValueValidator(0)],
        help_text='Calculated cost in USD'
    )
    
    # Status and Error Handling
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='success',
        db_index=True,
        help_text='Status of the LLM call'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text='Error message if the call failed'
    )
    
    # Metadata
    request_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Unique request ID from Groq API'
    )
    
    # User who made the request
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_traces',
        help_text='User who made this LLM call'
    )
    
    class Meta:
        verbose_name = 'LLM Trace'
        verbose_name_plural = 'LLM Traces'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['status']),
            models.Index(fields=['model_name']),
            models.Index(fields=['timestamp', 'status']),
        ]
    
    def __str__(self):
        return f'{self.model_name} - {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")} - {self.status}'
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-calculate total tokens if not set.
        """
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens
        super().save(*args, **kwargs)
    
    @property
    def latency_status(self):
        """
        Get latency status for UI color coding.
        
        Returns:
            str: 'good', 'warning', or 'critical' based on latency
        """
        if self.latency_ms < 500:
            return 'good'
        elif self.latency_ms < 1000:
            return 'warning'
        return 'critical'
    
    @property
    def prompt_preview(self):
        """
        Get a truncated preview of the prompt.
        
        Returns:
            str: First 100 characters of the prompt
        """
        if len(self.prompt) > 100:
            return self.prompt[:100] + '...'
        return self.prompt
    
    @property
    def response_preview(self):
        """
        Get a truncated preview of the response.
        
        Returns:
            str: First 100 characters of the response
        """
        if len(self.response) > 100:
            return self.response[:100] + '...'
        return self.response


class UserFeedback(models.Model):
    """
    Model to store user feedback for LLM responses.
    Allows users to rate responses and provide comments.
    """
    
    RATING_CHOICES = [
        (1, '👎 Poor'),
        (2, '😐 Fair'),
        (3, '👍 Good'),
        (4, '⭐ Great'),
        (5, '🌟 Excellent'),
    ]
    
    trace = models.ForeignKey(
        LLMTrace,
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text='The LLM trace this feedback is for'
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        help_text='User rating of the response (1-5)'
    )
    comment = models.TextField(
        blank=True,
        default='',
        help_text='Optional user comment'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the feedback was submitted'
    )
    
    class Meta:
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedbacks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Feedback for Trace {self.trace_id} - Rating: {self.rating}'
