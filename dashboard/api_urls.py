"""
API URL Configuration for Dashboard App

This module contains URL patterns for all REST API endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Trace endpoints
    path('traces/', views.LLMTraceListCreateView.as_view(), name='trace-list-create'),
    path('traces/<int:pk>/', views.LLMTraceDetailView.as_view(), name='trace-detail'),
    path('traces/recent/', views.RecentTracesView.as_view(), name='trace-recent'),
    path('traces/search/', views.SearchTracesView.as_view(), name='trace-search'),
    path('traces/export/', views.ExportTracesView.as_view(), name='trace-export'),
    
    # Analytics endpoints
    path('analytics/overview/', views.AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('analytics/charts/', views.AnalyticsChartsView.as_view(), name='analytics-charts'),
    
    # Configuration endpoints
    path('config/groq-key/', views.APIConfigurationView.as_view(), name='config-groq-key'),
    path('config/test-connection/', views.TestConnectionView.as_view(), name='config-test-connection'),
    path('config/models/', views.AvailableModelsView.as_view(), name='config-models'),
    path('config/default-model/', views.UpdateDefaultModelView.as_view(), name='config-default-model'),
    
    # Data management
    path('clear-data/', views.ClearDataView.as_view(), name='clear-data'),
    
    # Feedback endpoints
    path('feedback/', views.UserFeedbackCreateView.as_view(), name='feedback-create'),
    path('feedback/<int:trace_id>/', views.UserFeedbackListView.as_view(), name='feedback-list'),
    
    # Test LLM endpoint
    path('test-llm/', views.TestLLMView.as_view(), name='test-llm'),
]
