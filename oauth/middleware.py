import threading
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

_thread_locals = threading.local()
BYPASS_AUTHENTICATION = ['/', '/auth/jwt/create']


def get_current_user():
    return getattr(_thread_locals, 'user', None)


class ThreadLocalMiddleware:
    """
    Middleware to make the current request globally accessible.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.path not in BYPASS_AUTHENTICATION:
                jwt_authenticator = JWTAuthentication()
                result = jwt_authenticator.authenticate(request)
                if result is not None:
                    user, _ = result
                    if user:
                        _thread_locals.user = user
                        request.user = user
        except AuthenticationFailed:
            request.user = None

        response = self.get_response(request)
        return response
