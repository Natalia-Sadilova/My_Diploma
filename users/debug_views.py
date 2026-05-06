class HawkStatusView(APIView):
    """
    Проверка статуса интеграции с Hawk
    
    GET /api/v1/users/debug/hawk/status/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.conf import settings
        
        return Response({
            'hawk_configured': bool(settings.HAWK_DSN),
            'environment': getattr(settings, 'HAWK_ENVIRONMENT', 'not set'),
            'dsn_prefix': settings.HAWK_DSN[:30] + '...' if settings.HAWK_DSN else None,
            'message': 'Hawk is ready to capture errors!' if settings.HAWK_DSN else 'HAWK_DSN not configured'
        })