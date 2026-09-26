import os
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound

logger = logging.getLogger(__name__)


def spa_index_view(request):
    """
    Serves the Single Page Application (SPA) entry point (index.html).
    All non-API frontend routes (e.g. /, /transactions, /analytics, /payees, /settings, /login)
    are routed here so client-side React Router handles navigation seamlessly.
    """
    client_dir = getattr(settings, 'CLIENT_DIST_DIR', None)
    if client_dir:
        index_file = os.path.join(client_dir, 'index.html')
        if os.path.isfile(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                response = HttpResponse(content, content_type='text/html')
                # index.html should not be cached by browser so hash updates take effect immediately
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            except Exception as e:
                logger.error("Error reading frontend index.html: %s", e)
                return HttpResponse(f"Internal server error reading frontend index: {e}", status=500)

    return HttpResponseNotFound(
        """<!DOCTYPE html>
<html>
<head><title>CoinCraft • Frontend Build Required</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; background: #0f172a; color: #f8fafc; text-align: center;">
    <h2>Frontend bundle not found</h2>
    <p>Please compile the client app by running <code>npm run build</code> in <code>personalfinance-web</code></p>
</body>
</html>""",
        content_type='text/html'
    )
