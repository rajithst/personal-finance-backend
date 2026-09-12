from unittest.mock import MagicMock

import pytest
from django.http import HttpResponse
from rest_framework import status

from oauth.middleware import ThreadLocalMiddleware, get_current_user, clear_current_user
from oauth.views import PasswordResetWithoutEmailView


class TestThreadLocalSecurity:
    def test_thread_local_cleanup_after_request(self, mocker):
        # Simulate authenticated request
        mock_user = MagicMock(id=1, username="testuser")
        mock_jwt = mocker.patch("oauth.middleware.JWTAuthentication")
        mock_jwt.return_value.authenticate.return_value = (mock_user, "mock_token")

        seen_user_during_request = []

        def dummy_view(request):
            # Inside the view, get_current_user() should return mock_user
            seen_user_during_request.append(get_current_user())
            return HttpResponse("OK")

        middleware = ThreadLocalMiddleware(get_response=dummy_view)

        mock_request = MagicMock()
        mock_request.path = "/finance/transactions/list/"

        response = middleware(mock_request)
        assert response.status_code == 200

        # Verify user was available during request
        assert len(seen_user_during_request) == 1
        assert seen_user_during_request[0] == mock_user

        # CRITICAL: Verify thread-local user was cleared after request execution
        assert get_current_user() is None

    def test_thread_local_cleanup_on_exception(self, mocker):
        mock_user = MagicMock(id=2, username="erroruser")
        mock_jwt = mocker.patch("oauth.middleware.JWTAuthentication")
        mock_jwt.return_value.authenticate.return_value = (mock_user, "mock_token")

        def exploding_view(request):
            assert get_current_user() == mock_user
            raise RuntimeError("View crashed!")

        middleware = ThreadLocalMiddleware(get_response=exploding_view)

        mock_request = MagicMock()
        mock_request.path = "/finance/transactions/list/"

        with pytest.raises(RuntimeError, match="View crashed!"):
            middleware(mock_request)

        # CRITICAL: Verify thread-local user was cleared even after an uncaught exception
        assert get_current_user() is None


class TestPasswordResetSecurity:
    def test_password_reset_without_email_blocked_in_production(self, mocker):
        view = PasswordResetWithoutEmailView()
        mock_request = MagicMock()
        mock_request.user = MagicMock(is_staff=False)
        mock_request.data = {"username": "target_user"}

        mocker.patch("django.conf.settings.DEBUG", False)

        response = view.post(mock_request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "disabled in production" in response.data["error"]


class TestRequestManagerSafety:
    def test_request_manager_safe_when_no_user(self, mocker):
        from oauth.util.request_manager import RequestManager
        from django.db import models

        mocker.patch("oauth.util.request_manager.get_current_user", return_value=None)
        mgr = RequestManager()
        mgr.model = MagicMock()

        # Mock super().get_queryset()
        mock_qs = MagicMock()
        with mocker.patch.object(models.Manager, "get_queryset", return_value=mock_qs):
            qs = mgr.get_queryset()
            assert qs == mock_qs

    def test_request_manager_filters_by_user_when_authenticated(self, mocker):
        from oauth.util.request_manager import RequestManager
        from django.db import models

        mock_user = MagicMock(id=42, is_authenticated=True)
        mocker.patch("oauth.util.request_manager.get_current_user", return_value=mock_user)
        mgr = RequestManager()
        mgr.model = MagicMock()

        mock_qs = MagicMock()
        mock_filtered_qs = MagicMock()
        mock_qs.filter.return_value = mock_filtered_qs
        with mocker.patch.object(models.Manager, "get_queryset", return_value=mock_qs):
            qs = mgr.get_queryset()
            mock_qs.filter.assert_called_once_with(user_id=42)
            assert qs == mock_filtered_qs
