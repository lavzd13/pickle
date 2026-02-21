from django.utils.cache import add_never_cache_headers


class NoCacheForAuthenticatedMiddleware:
    """
    Middleware to prevent browser caching of pages for authenticated users.
    This prevents the back button from showing cached authenticated pages after logout.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add no-cache headers for authenticated users
        if request.user.is_authenticated:
            add_never_cache_headers(response)
            # Also add additional cache control headers for extra safety
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
