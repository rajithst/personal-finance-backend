from unittest.mock import MagicMock, patch
from common.constants import (
    ACCOUNT_TYPE_BANK_ACCOUNT,
    ACCOUNT_TYPE_CREDIT_CARD,
    CREDIT_CARD_PROVIDER_RAKUTEN,
)
from finance.settings.service.settings_service import SettingsService


class TestSettingsService:
    def test_account_types_excludes_investment(self):
        service = SettingsService()
        types = service.get_account_types()
        assert ACCOUNT_TYPE_BANK_ACCOUNT in types
        assert ACCOUNT_TYPE_CREDIT_CARD in types
        # Verify investment account was removed
        assert "investment_account" not in [t.lower() for t in types]
        assert len(types) == 2

    def test_account_providers_excludes_investment(self):
        service = SettingsService()
        providers = service.get_account_providers()
        provider_types = [p['provider_type'] for p in providers]
        assert ACCOUNT_TYPE_CREDIT_CARD in provider_types
        assert ACCOUNT_TYPE_BANK_ACCOUNT in provider_types
        for p in providers:
            assert "invest" not in p['provider_type'].lower()

    @patch("finance.settings.service.settings_service.Account.objects.all")
    @patch("finance.settings.service.settings_service.ResponseAccountSerializer")
    def test_get_accounts_and_credit_accounts_consistency(self, mock_serializer_cls, mock_account_all):
        mock_account_all.return_value = []
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'name': 'Card1'}]
        mock_serializer_cls.return_value = mock_serializer

        service = SettingsService()
        accounts = service.get_accounts()
        credit_accounts = service.get_credit_accounts()

        assert accounts == [{'id': 1, 'name': 'Card1'}]
        assert credit_accounts == accounts
