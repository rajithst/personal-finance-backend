import logging

from django.db import transaction
from django.db.models import Case, When, IntegerField

from common.transaction_const import (
    INCOME_CATEGORY_TYPE,
    SAVINGS_CATEGORY_TYPE,
    EXPENSE_CATEGORY_TYPE,
    PAYMENT_CATEGORY_TYPE,
)
from finance.payees.models import DestinationMap
from finance.payees.serializers import DestinationMapSerializer, ResponseDestinationMapSerializer
from finance.transactions.models import Transaction
from finance.transactions.serializers import ResponseTransactionSerializer


class PayeeService:

    def get_custom_queryset(self):
        """
        Gets the custom queryset for the payee.

        Returns:
            QuerySet: The custom queryset for the payee.
        """
        queryset = (DestinationMap.objects.select_related('category', 'subcategory')
        .order_by(
            Case(
                When(category_id__isnull=True, then=1),
                When(category_id__isnull=False, then=0),
                output_field=IntegerField(),
            ),
            'category_id',
            'subcategory_id'))
        return queryset

    def get_by_id(self, pk):
        try:
            return self.get_custom_queryset().get(pk=pk)
        except DestinationMap.DoesNotExist:
            return None

    def get_by_name(self, name):
        return self.get_custom_queryset().filter(destination=name).first()

    def get_payee_by_id_or_name(self, request_data, include_transactions=True, transaction_limit=None):
        payee_id = request_data.get('id', None)
        name = request_data.get('name', None)
        instance = None
        if payee_id:
            instance = self.get_by_id(payee_id)
        elif name:
            instance = self.get_by_name(name)

        if not instance:
            return {'payee': None, 'transactions': None}

        payee_serializer = ResponseDestinationMapSerializer(instance)
        if include_transactions:
            transactions = Transaction.objects.select_related('category', 'subcategory', 'account').filter(
                destination=instance.destination)
            if transaction_limit:
                transactions = transactions[:transaction_limit]
            transaction_serializer = ResponseTransactionSerializer(transactions, many=True)
            transactions_data = transaction_serializer.data
        else:
            transactions_data = []

        return {'payee': payee_serializer.data, 'transactions': transactions_data}

    def get_payees(self):
        queryset = self.get_custom_queryset()
        serializer = ResponseDestinationMapSerializer(queryset, many=True)
        return serializer.data

    def update_payee(self, request_data):
        """
        Updates the payee.

        Args:
            request_data (dict): The request data.

        Returns:
            tuple: A tuple containing a boolean value and the updated payee.
        """
        payee_id = request_data.get('id')
        merge_ids = request_data.get('merge_ids')
        new_destination = request_data.get('destination')
        new_alias = request_data.get('destination_eng')
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        category_type = request_data.get('category_type')

        exist_settings = DestinationMap.objects.filter(pk=payee_id).first()
        if not exist_settings:
            return False, {'id': f'Payee with id {payee_id} not found.'}

        is_payee_renamed = new_destination and (new_destination != exist_settings.destination)
        destination = new_destination if is_payee_renamed else exist_settings.destination
        target_destinations = [exist_settings.destination]

        serializer = DestinationMapSerializer(exist_settings, data=request_data, partial=True)
        if not serializer.is_valid():
            return False, serializer.errors

        if merge_ids:
            merge_records = DestinationMap.objects.filter(id__in=merge_ids)
            target_destinations.extend(list(merge_records.values_list('destination_original', flat=True)))

        try:
            with transaction.atomic():
                serializer.save()
                update_params = {
                    'destination': destination,
                    'alias': new_alias,
                    'category_id': category,
                    'subcategory_id': subcategory,
                }
                flag_mapping = {
                    INCOME_CATEGORY_TYPE: {'is_income': True, 'is_expense': False, 'is_saving': False, 'is_payment': False},
                    SAVINGS_CATEGORY_TYPE: {'is_income': False, 'is_expense': True, 'is_saving': True, 'is_payment': False},
                    EXPENSE_CATEGORY_TYPE: {'is_income': False, 'is_expense': True, 'is_saving': False, 'is_payment': False},
                    PAYMENT_CATEGORY_TYPE: {'is_income': False, 'is_expense': True, 'is_saving': False, 'is_payment': True},
                }
                if category_type in flag_mapping:
                    update_params.update(flag_mapping[category_type])

                Transaction.objects.filter(destination__in=target_destinations).update(**update_params)
                if merge_ids:
                    DestinationMap.objects.filter(id__in=merge_ids).delete()

            payee_details = self.get_payee_by_id_or_name({'id': payee_id}, include_transactions=False)
            return True, payee_details
        except Exception as e:
            logging.exception("An unexpected error occurred while updating payee: %s", e)
            return False, {'error': str(e)}

