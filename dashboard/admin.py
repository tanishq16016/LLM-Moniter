"""
Django Admin Configuration for Dashboard App

This module configures the Django admin interface for all dashboard models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import LLMTrace, APIConfiguration, UserFeedback


@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    """
    Admin configuration for APIConfiguration model.
    """
    
    list_display = ('__str__', 'is_active', 'default_model', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Status', {
            'fields': ('is_active', 'default_model')
        }),
        ('API Key', {
            'fields': ('groq_api_key_encrypted',),
            'description': 'API key is stored encrypted. Use the dashboard settings page to update.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding new instances (singleton pattern)."""
        return not APIConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton instance."""
        return False


@admin.register(LLMTrace)
class LLMTraceAdmin(admin.ModelAdmin):
    """
    Admin configuration for LLMTrace model.
    """
    
    list_display = (
        'id',
        'timestamp',
        'model_name',
        'status_badge',
        'total_tokens',
        'latency_display',
        'cost_display',
    )
    list_filter = ('status', 'model_name', 'timestamp')
    search_fields = ('prompt', 'response', 'error_message')
    readonly_fields = (
        'timestamp',
        'request_id',
        'prompt_formatted',
        'response_formatted'
    )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('timestamp', 'model_name', 'status', 'request_id')
        }),
        ('Request/Response', {
            'fields': ('prompt_formatted', 'response_formatted', 'error_message'),
            'classes': ('wide',)
        }),
        ('Metrics', {
            'fields': ('input_tokens', 'output_tokens', 'total_tokens', 'latency_ms', 'cost_usd')
        }),
    )
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        if obj.status == 'success':
            color = '#198754'
            icon = '✓'
        else:
            color = '#dc3545'
            icon = '✗'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            color, icon, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def latency_display(self, obj):
        """Display latency with color coding."""
        if obj.latency_ms < 500:
            color = '#198754'
        elif obj.latency_ms < 1000:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.0f}ms</span>',
            color, obj.latency_ms
        )
    latency_display.short_description = 'Latency'
    latency_display.admin_order_field = 'latency_ms'
    
    def cost_display(self, obj):
        """Display cost formatted as USD."""
        return f'${obj.cost_usd:.6f}'
    cost_display.short_description = 'Cost'
    cost_display.admin_order_field = 'cost_usd'
    
    def prompt_formatted(self, obj):
        """Display prompt in a formatted text area."""
        return format_html(
            '<pre style="white-space: pre-wrap; word-wrap: break-word; '
            'max-height: 300px; overflow-y: auto; background: #f8f9fa; '
            'padding: 10px; border-radius: 5px;">{}</pre>',
            obj.prompt
        )
    prompt_formatted.short_description = 'Prompt'
    
    def response_formatted(self, obj):
        """Display response in a formatted text area."""
        return format_html(
            '<pre style="white-space: pre-wrap; word-wrap: break-word; '
            'max-height: 300px; overflow-y: auto; background: #f8f9fa; '
            'padding: 10px; border-radius: 5px;">{}</pre>',
            obj.response
        )
    response_formatted.short_description = 'Response'


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserFeedback model.
    """
    
    list_display = ('id', 'trace', 'rating_display', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment', 'trace__prompt')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 50
    
    fieldsets = (
        ('Feedback', {
            'fields': ('trace', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        """Display rating as stars."""
        stars = '⭐' * obj.rating
        return format_html('<span style="font-size: 14px;">{}</span>', stars)
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'
    
    def comment_preview(self, obj):
        """Display truncated comment."""
        if obj.comment and len(obj.comment) > 50:
            return obj.comment[:50] + '...'
        return obj.comment or '-'
    comment_preview.short_description = 'Comment'


# Customize admin site header
admin.site.site_header = 'LLM Observability Dashboard'
admin.site.site_title = 'LLM Monitor Admin'
admin.site.index_title = 'Dashboard Administration'
