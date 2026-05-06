from rest_framework.throttling import AnonRateThrottle

class RegistrationAnonRateThrottle(AnonRateThrottle):
    scope = 'registration' # Уникальное имя для этого лимита