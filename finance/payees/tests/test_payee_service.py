from unittest.mock import MagicMock, patch
import pytest

from finance.payees.models import DestinationMap
from finance.payees.service.payee_service import PayeeService


class TestPayeeService:
    @patch.object(PayeeService, "get_custom_queryset")
    def test_get_by_id_not_found_returns_none(self, mock_qs):
        mock_qs.return_value.get.side_effect = DestinationMap.DoesNotExist
        service = PayeeService()
        assert service.get_by_id(999) is None

    @patch.object(PayeeService, "get_custom_queryset")
    def test_get_by_name_not_found_returns_none(self, mock_qs):
        mock_qs.return_value.filter.return_value.first.return_value = None
        service = PayeeService()
        assert service.get_by_name("UnknownMerchant") is None

    @patch.object(PayeeService, "get_by_id")
    @patch("finance.payees.service.payee_service.ResponseDestinationMapSerializer")
    def test_get_payee_by_id_without_transactions(self, mock_serializer_cls, mock_get_by_id):
        mock_instance = MagicMock()
        mock_instance.destination = "Starbucks"
        mock_get_by_id.return_value = mock_instance

        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'destination': 'Starbucks'}
        mock_serializer_cls.return_value = mock_serializer

        service = PayeeService()
        result = service.get_payee_by_id_or_name({'id': 1}, include_transactions=False)

        assert result['payee'] == {'id': 1, 'destination': 'Starbucks'}
        assert result['transactions'] == []

    @patch.object(DestinationMap.objects, "filter")
    def test_update_payee_not_found(self, mock_filter):
        mock_filter.return_value.first.return_value = None
        service = PayeeService()
        success, response = service.update_payee({'id': 999})

        assert success is False
        assert "not found" in response['id']
