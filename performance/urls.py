from django.urls import path
from .views import PerformanceTestView

urlpatterns = [
    path('test/', PerformanceTestView.as_view(), name='performance-test'),
]