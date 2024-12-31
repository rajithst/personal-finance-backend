import logging

from django.db.models import Case, When, IntegerField

from transactions.common.transaction_const import INCOME_CATEGORY_TYPE, SAVINGS_CATEGORY_TYPE, EXPENSE_CATEGORY_TYPE, \
    PAYMENT_CATEGORY_TYPE
from transactions.models import DestinationMap, Transaction
from transactions.serializers.response_serializers import ResponseDestinationMapSerializer, \
    ResponseTransactionSerializer


class PayeeService:

    def get_custom_queryset(self):
        """
        Gets the custom queryset for the payee.

        Returns:
            QuerySet: The custom queryset for the payee.
        """
        queryset = DestinationMap.objects.select_related('category', 'subcategory').order_by(
            Case(
                When(category_id__isnull=True, then=1),
                When(category_id__isnull=False, then=0),
                output_field=IntegerField(),
            ),
            'category_id',
            'subcategory_id')
        return queryset

    def get_by_id(self, pk):
        instance = self.get_custom_queryset().get(pk=pk)
        return instance

    def get_by_name(self, name):
        instance = self.get_custom_queryset().get(destination=name)
        return instance

    def get_payee_details(self, request_data):
        """
        Gets the payee details.

        Args:
            request_data (dict): The request data.

        Returns:
            dict: The payee details.
        """
        payee_id = request_data.get('id', None)
        name = request_data.get('name', None)
        instance = None
        if payee_id:
            instance = self.get_by_id(payee_id)
        elif name:
            instance = self.get_by_name(name)

        if not instance:
            return {'payee': None, 'transactions': None}

        transactions = Transaction.objects.select_related('category', 'subcategory', 'account').filter(
            destination=instance.destination)

        payee_serializer = ResponseDestinationMapSerializer(instance)
        transaction_serializer = ResponseTransactionSerializer(transactions, many=True)
        return {'payee': payee_serializer.data, 'transactions': transaction_serializer.data}

    def get_payees(self, request_data):
        """
        Gets the payees.

        Args:
            request_data (dict): The request data.

        Returns:
            dict: The payees.
        """
        payee_id = request_data.get('id', None)
        if payee_id:
            instance = self.get_by_id(payee_id)
            payee_serializer = ResponseDestinationMapSerializer(instance)
            return payee_serializer.data
        else:
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

        exist_settings = DestinationMap.objects.get(pk=payee_id)

        is_payee_renamed = request_data.get('destination') != exist_settings.destination
        destination = new_destination if is_payee_renamed else exist_settings.destination
        target_destinations = [exist_settings.destination]
        serializer = ResponseDestinationMapSerializer(exist_settings, data=request_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            if merge_ids:
                merge_records = DestinationMap.objects.filter(id__in=merge_ids)
                target_destinations.extend(list(merge_records.values_list('destination_original', flat=True)))

            try:
                update_params = {
                    'destination': destination,
                    'alias': new_alias,
                    'category_id': category,
                    'subcategory_id': subcategory,
                }
                if category_type == INCOME_CATEGORY_TYPE:
                    update_params['is_income'] = 1
                    update_params['is_expense'] = 0
                    update_params['is_saving'] = 0
                    update_params['is_payment'] = 0
                elif category_type == SAVINGS_CATEGORY_TYPE:
                    update_params['is_income'] = 0
                    update_params['is_expense'] = 1
                    update_params['is_saving'] = 1
                    update_params['is_payment'] = 0
                elif category_type == EXPENSE_CATEGORY_TYPE:
                    update_params['is_income'] = 0
                    update_params['is_expense'] = 1
                    update_params['is_saving'] = 0
                    update_params['is_payment'] = 0
                elif category_type == PAYMENT_CATEGORY_TYPE:
                    update_params['is_income'] = 0
                    update_params['is_expense'] = 1
                    update_params['is_saving'] = 0
                    update_params['is_payment'] = 1

                Transaction.objects.filter(destination__in=target_destinations).update(
                    **update_params)
                DestinationMap.objects.filter(id__in=merge_ids).delete()
                return True, serializer.data
            except Exception as e:
                logging.exception("An unexpected error occurred:", e)
                return False, serializer.errors
