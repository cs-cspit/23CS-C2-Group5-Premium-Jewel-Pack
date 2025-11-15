"""
Custom middleware for session security and cache control.
"""

class SessionSecurityMiddleware:
    """
    Middleware to handle session security and prevent cached access after logout.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers for authenticated pages
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['Last-Modified'] = '0'
            response['Vary'] = 'Cookie'
        
        return response

    def process_request(self, request):
        """
        Process request to ensure session validity.
        """
        # Check if session is valid
        if request.user.is_authenticated and not request.session.session_key:
            # Session is invalid, clear user
            from django.contrib.auth import logout
            logout(request)
        
        return None