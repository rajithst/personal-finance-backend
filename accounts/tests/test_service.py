from unittest.mock import MagicMock, patch
import pytest

from accounts.models import Account
from accounts.service.account_service import AccountService, CreditAccountService


class TestAccountService:
    def test_alias_compatibility(self):
        assert CreditAccountService is AccountService

    @patch("accounts.service.account_service.AccountSerializer")
    def test_create_account(self, mock_serializer_cls):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        saved_instance = MagicMock()
        mock_serializer.save.return_value = saved_instance
        mock_serializer_cls.return_value = mock_serializer

        with patch("accounts.service.account_service.ResponseAccountSerializer") as mock_resp_cls:
            mock_resp = MagicMock()
            mock_resp.data = {'id': 1, 'account_name': 'Test Bank'}
            mock_resp_cls.return_value = mock_resp

            service = AccountService()
            result = service.create_account({'account_name': 'Test Bank'})

            mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
            assert result == {'id': 1, 'account_name': 'Test Bank'}

    @patch.object(Account.objects, "filter")
    def test_update_account_not_found(self, mock_filter):
        mock_filter.return_value.first.return_value = None
        service = AccountService()

        with pytest.raises(Account.DoesNotExist, match="Account with id 999 does not exist."):
            service.update_account({'id': 999, 'account_name': 'Updated'})
