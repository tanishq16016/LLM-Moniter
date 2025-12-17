"""
Dashboard App Configuration
"""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configuration for the Dashboard application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = 'LLM Observability Dashboard'
    
    def ready(self):
        """
        Called when the app is ready.
        Import signals here if needed.
        """
        import dashboard.signals  # noqa: F401
