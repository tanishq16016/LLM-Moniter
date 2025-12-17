"""
Django REST Framework Serializers for Dashboard App

This module contains all serializers for converting model instances
to JSON and handling data validation for API endpoints.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import LLMTrace, APIConfiguration, UserFeedback


class LLMTraceSerializer(serializers.ModelSerializer):
    """
    Serializer for LLMTrace model.
    Handles both read and write operations for trace records.
    """
    
    latency_status = serializers.ReadOnlyField()
    prompt_preview = serializers.ReadOnlyField()
    response_preview = serializers.ReadOnlyField()
    
    class Meta:
        model = LLMTrace
        fields = [
            'id',
            'timestamp',
            'model_name',
            'prompt',
            'response',
            'input_tokens',
            'output_tokens',
            'total_tokens',
            'latency_ms',
            'cost_usd',
            'status',
            'error_message',
            'request_id',
            'latency_status',
            'prompt_preview',
            'response_preview',
        ]
        read_only_fields = ['id', 'timestamp', 'request_id']
    
    def validate_model_name(self, value):
        """Validate that the model name is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Model name cannot be empty.")
        return value.strip()
    
    def validate_prompt(self, value):
        """Validate that the prompt is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Prompt cannot be empty.")
        return value.strip()
    
    def validate_status(self, value):
        """Validate status is one of allowed choices."""
        allowed = ['success', 'error']
        if value not in allowed:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(allowed)}"
            )
        return value


class LLMTraceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for creating new LLM traces.
    Has less strict validation for programmatic creation.
    """
    
    class Meta:
        model = LLMTrace
        fields = [
            'model_name',
            'prompt',
            'response',
            'input_tokens',
            'output_tokens',
            'total_tokens',
            'latency_ms',
            'cost_usd',
            'status',
            'error_message',
            'request_id',
        ]
    
    def create(self, validated_data):
        """Create a new trace with automatic timestamp."""
        validated_data['timestamp'] = timezone.now()
        return super().create(validated_data)


class LLMTraceListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing traces.
    Excludes full prompt/response for performance.
    """
    
    latency_status = serializers.ReadOnlyField()
    prompt_preview = serializers.ReadOnlyField()
    response_preview = serializers.ReadOnlyField()
    user_identifier = serializers.SerializerMethodField()
    
    class Meta:
        model = LLMTrace
        fields = [
            'id',
            'timestamp',
            'model_name',
            'prompt_preview',
            'response_preview',
            'total_tokens',
            'latency_ms',
            'latency_status',
            'cost_usd',
            'status',
            'user_identifier',
        ]
    
    def get_user_identifier(self, obj):
        """Get the username from the trace's user field."""
        if obj.user:
            return obj.user.username
        return 'Anonymous'


class APIConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for APIConfiguration model.
    Never exposes the actual API key in responses.
    """
    
    has_api_key = serializers.SerializerMethodField()
    api_key_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = APIConfiguration
        fields = [
            'is_active',
            'default_model',
            'updated_at',
            'has_api_key',
            'api_key_masked',
        ]
        read_only_fields = ['updated_at']
    
    def get_has_api_key(self, obj):
        """Check if an API key is configured."""
        return obj.has_api_key()
    
    def get_api_key_masked(self, obj):
        """Return masked version of API key for display."""
        key = obj.get_api_key()
        if key and len(key) > 8:
            return key[:4] + '*' * (len(key) - 8) + key[-4:]
        elif key:
            return '*' * len(key)
        return None


class APIKeyUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating the Groq API key.
    """
    
    api_key = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Groq API key"
    )
    
    def validate_api_key(self, value):
        """Validate the API key format."""
        if not value or not value.strip():
            raise serializers.ValidationError("API key cannot be empty.")
        value = value.strip()
        # Groq API keys typically start with 'gsk_'
        if not value.startswith('gsk_'):
            raise serializers.ValidationError(
                "Invalid Groq API key format. Key should start with 'gsk_'."
            )
        return value
    
    def save(self):
        """Save the API key to the configuration."""
        config = APIConfiguration.load()
        config.set_api_key(self.validated_data['api_key'])
        config.save()
        return config


class TestLLMSerializer(serializers.Serializer):
    """
    Serializer for the test LLM endpoint.
    """
    
    prompt = serializers.CharField(
        required=True,
        max_length=10000,
        help_text="The prompt to send to the LLM"
    )
    model = serializers.CharField(
        required=False,
        max_length=100,
        help_text="The model to use (optional, uses default if not specified)"
    )
    
    def validate_prompt(self, value):
        """Validate the prompt is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Prompt cannot be empty.")
        return value.strip()


class AnalyticsOverviewSerializer(serializers.Serializer):
    """
    Serializer for analytics overview data.
    """
    
    total_requests_today = serializers.IntegerField()
    total_requests_week = serializers.IntegerField()
    total_requests_month = serializers.IntegerField()
    total_requests_all = serializers.IntegerField()
    average_latency_ms = serializers.FloatField()
    total_tokens = serializers.IntegerField()
    total_input_tokens = serializers.IntegerField()
    total_output_tokens = serializers.IntegerField()
    total_cost_usd = serializers.DecimalField(max_digits=10, decimal_places=4)
    error_rate_percent = serializers.FloatField()
    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    top_models = serializers.ListField()


class ChartDataSerializer(serializers.Serializer):
    """
    Serializer for chart data responses.
    """
    
    tokens_over_time = serializers.ListField()
    latency_trends = serializers.ListField()
    error_rate_over_time = serializers.ListField()
    cost_by_model = serializers.ListField()
    requests_by_model = serializers.ListField()
    requests_by_hour = serializers.ListField()


class ExportSerializer(serializers.Serializer):
    """
    Serializer for data export parameters.
    """
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    model_name = serializers.CharField(required=False, max_length=100)
    status = serializers.ChoiceField(
        required=False,
        choices=['success', 'error', 'all'],
        default='all'
    )
    format = serializers.ChoiceField(
        required=False,
        choices=['csv', 'json'],
        default='csv'
    )


class UserFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for UserFeedback model.
    """
    
    class Meta:
        model = UserFeedback
        fields = ['id', 'trace', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserFeedbackCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating user feedback.
    """
    
    class Meta:
        model = UserFeedback
        fields = ['trace', 'rating', 'comment']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
