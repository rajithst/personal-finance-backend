"""
URL configuration for personalfinance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path

from core.views import spa_index_view
from django.db import connection


def health_check(request):
    data = {'status': 'healthy', 'service': 'coincraftservice'}
    if request.GET.get('db') == '1':
        try:
            connection.ensure_connection()
            data['database'] = 'connected'
        except Exception as e:
            data['database'] = 'error'
            data['database_error'] = f"{type(e).__name__}: {str(e)}"
    return JsonResponse(data)


admin.site.site_header = 'Personal Finance Administration'
admin.site.index_title = 'Welcome to Personal Finance'
urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('finance/transaction/', include('finance.transactions.urls')),
    path('finance/category/', include('finance.categories.urls')),
    path('finance/payees/', include('finance.payees.urls')),
    path('finance/dashboard/', include('finance.dashboard.urls')),
    path('finance/analytics/', include('finance.analytics.urls')),
    path('finance/settings/', include('finance.settings.urls')),
    path('finance/career/', include('finance.career.urls')),
    path('logs/', include('changelog.urls')),
    path('oauth/', include('oauth.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

def media_local_compat_view(request, path):
    from django.views.static import serve
    clean_path = path.lstrip('/')
    return serve(request, clean_path, document_root=settings.MEDIA_ROOT)

def media_career_docs_fallback_view(request, path):
    """
    Fallback view for /media/career_docs/<path> in production.
    If the file exists locally, serve it.
    If the file is recorded in CareerDocument, stream it via open_document_stream.
    """
    import os
    from django.http import FileResponse, JsonResponse
    clean_path = path.lstrip('/')
    local_path = os.path.join(settings.MEDIA_ROOT, 'career_docs', clean_path)
    if os.path.exists(local_path):
        import mimetypes
        content_type = mimetypes.guess_type(local_path)[0] or 'application/pdf'
        return FileResponse(open(local_path, 'rb'), content_type=content_type)

    try:
        from finance.career.models import CareerDocument
        from finance.career.services.storage_service import open_document_stream
        doc = CareerDocument.objects.filter(file__endswith=clean_path).first()
        if not doc:
            filename = os.path.basename(clean_path)
            doc = CareerDocument.objects.filter(file_name_original=filename).first()
        if doc:
            stream_info = open_document_stream(doc)
            if stream_info:
                stream, content_type, orig_filename, size = stream_info
                resp = FileResponse(stream, content_type=content_type)
                resp['Content-Disposition'] = f'inline; filename="{orig_filename}"'
                if size:
                    resp['Content-Length'] = str(size)
                return resp
    except Exception:
        pass

    return JsonResponse({'status': False, 'message': 'Document not found on storage. Please re-upload this document.'}, status=404)

urlpatterns += [
    re_path(r'^media/career_docs/(?P<path>.*)$', media_career_docs_fallback_view, name='media-career-docs-fallback'),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/local:/?(?P<path>.*)$', media_local_compat_view),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Single Page Application (SPA) catch-all route (must be the LAST pattern):
# Routes root and all client-side navigation (e.g. /, /transactions, /analytics, /settings)
# to index.html while preserving backend APIs, admin, health, static, media, and assets.
urlpatterns += [
    re_path(r'^(?!api/|admin/|health/|finance/|accounts/|logs/|oauth/|auth/|static/|media/|assets/).*$', spa_index_view, name='spa-client'),
]
