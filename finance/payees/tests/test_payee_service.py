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

    def test_response_destination_map_serializer_accounting_flags(self):
        from finance.payees.serializers import ResponseDestinationMapSerializer
        from common.transaction_const import PAYMENT_CATEGORY_TYPE, EXPENSE_CATEGORY_TYPE

        # Case 1: ATM withdrawal should be both payment and expense
        atm_obj = MagicMock(spec=DestinationMap)
        atm_obj.destination = "ATM Withdrawal"
        atm_obj.destination_original = "ＡＴＭ（５９９）"
        atm_obj.destination_eng = "ATM Withdrawal"
        atm_obj.keywords = "ATM, 7BK"
        atm_obj.category = None
        atm_obj.category_type = PAYMENT_CATEGORY_TYPE
        atm_obj.subcategory = None

        atm_data = ResponseDestinationMapSerializer(atm_obj).data
        assert atm_data['is_payment'] is True
        assert atm_data['is_expense'] is True
        assert atm_data['is_income'] is False
        assert atm_data['is_saving'] is False

        # Case 2: Direct bank living expenses (Rent Payment) should be both payment and expense
        rent_obj = MagicMock(spec=DestinationMap)
        rent_obj.destination = "Rent Payment"
        rent_obj.destination_original = "ＳＭＢＣ（ヤチン）"
        rent_obj.destination_eng = "Rent"
        rent_obj.keywords = "ヤチン"
        rent_obj.category = None
        rent_obj.category_type = EXPENSE_CATEGORY_TYPE
        rent_obj.subcategory = None

        rent_data = ResponseDestinationMapSerializer(rent_obj).data
        assert rent_data['is_payment'] is True
        assert rent_data['is_expense'] is True

        # Case 3: Credit Card bill settlements should be payment ONLY, NOT expense
        card_obj = MagicMock(spec=DestinationMap)
        card_obj.destination = "Rakuten Card Payment"
        card_obj.destination_original = "ラクテンカ−ドサ−ビス"
        card_obj.destination_eng = "Rakuten Card Payment"
        card_obj.keywords = "ラクテンカ−ド"
        card_obj.category = None
        card_obj.category_type = PAYMENT_CATEGORY_TYPE
        card_obj.subcategory = None

        card_data = ResponseDestinationMapSerializer(card_obj).data
        assert card_data['is_payment'] is True
        assert card_data['is_expense'] is False

