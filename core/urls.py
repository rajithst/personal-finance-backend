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
from django.urls import path, include


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
    path('logs/', include('changelog.urls')),
    path('oauth/', include('oauth.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
