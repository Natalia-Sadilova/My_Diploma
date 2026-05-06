from django.urls import path
from .views import PerformanceTestView, PartnerOrdersProfilerView

urlpatterns = [
    path('test/', PerformanceTestView.as_view(), name='performance-test'),
    path('profile/partner-orders/', PartnerOrdersProfilerView.as_view(), name='profile-partner-orders'),
]