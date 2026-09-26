import pytest
from django.test import Client


@pytest.mark.django_db
class TestSpaServing:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        self.client = Client()

    def test_root_serves_spa_index(self):
        response = self.client.get('/')
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('Content-Type', '')
        assert response.headers.get('Cache-Control') == 'no-cache, no-store, must-revalidate'
        assert b'<div id="root">' in response.content or b'CoinCraft' in response.content

    def test_client_side_routes_serve_spa_index(self):
        routes = ['/transactions', '/analytics', '/settings', '/payees', '/categories', '/login']
        for route in routes:
            response = self.client.get(route)
            assert response.status_code == 200
            assert 'text/html' in response.headers.get('Content-Type', '')

    def test_health_api_not_intercepted_by_spa(self):
        response = self.client.get('/health/')
        assert response.status_code == 200
        assert 'application/json' in response.headers.get('Content-Type', '')
        assert response.json().get('status') == 'healthy'

    def test_admin_not_intercepted_by_spa(self):
        response = self.client.get('/admin/')
        # Should redirect to admin login
        assert response.status_code == 302
        assert '/admin/login/' in response.headers.get('Location', '')

    def test_missing_asset_returns_404_not_spa_html(self):
        response = self.client.get('/assets/non-existent-script.js')
        assert response.status_code == 404
