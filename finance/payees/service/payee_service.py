import logging

from django.db import transaction
from django.db.models import Case, When, IntegerField, Q, Count, Sum, Max

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
            if name and include_transactions:
                clean_name = name.strip()
                transactions = Transaction.objects.select_related('category', 'subcategory', 'account').filter(
                    Q(destination__iexact=clean_name) | Q(destination_original__iexact=clean_name),
                    is_deleted=False
                ).order_by('-date')
                if transaction_limit:
                    transactions = transactions[:transaction_limit]
                transaction_serializer = ResponseTransactionSerializer(transactions, many=True)
                return {
                    'payee': {
                        'id': 0,
                        'destination': clean_name,
                        'keywords': '',
                        'category': None,
                        'category_text': None
                    },
                    'transactions': transaction_serializer.data
                }
            return {'payee': None, 'transactions': None}

        payee_serializer = ResponseDestinationMapSerializer(instance)
        if include_transactions:
            clean_dest = instance.destination.strip() if instance.destination else ''
            transactions = Transaction.objects.select_related('category', 'subcategory', 'account').filter(
                Q(destination__iexact=clean_dest) | Q(destination_original__iexact=clean_dest),
                is_deleted=False
            ).order_by('-date')
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
        payee_data = [dict(item) for item in serializer.data]

        # Aggregate transaction statistics (count, total spend, last transaction date) per destination
        try:
            stats_rows = Transaction.objects.filter(is_deleted=False).values('destination').annotate(
                cnt=Count('id'),
                tot=Sum('amount'),
                last=Max('date')
            )
            stats_map = {}
            for r in stats_rows:
                dest = r.get('destination')
                if dest:
                    stats_map[dest.strip().lower()] = {
                        'transaction_count': r['cnt'],
                        'total_spend': float(r['tot'] or 0),
                        'last_transaction_date': str(r['last']) if r['last'] else None,
                    }

            for item in payee_data:
                dest = (item.get('destination') or '').strip().lower()
                dest_orig = (item.get('destination_original') or '').strip().lower()
                stats = stats_map.get(dest) or stats_map.get(dest_orig) or {
                    'transaction_count': 0,
                    'total_spend': 0.0,
                    'last_transaction_date': None,
                }
                item['transaction_count'] = stats['transaction_count']
                item['total_spend'] = stats['total_spend']
                item['last_transaction_date'] = stats['last_transaction_date']
        except Exception as e:
            logging.warning("Failed to aggregate payee transaction stats: %s", e)

        return payee_data

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
            for rec in merge_records:
                if rec.destination and rec.destination not in target_destinations:
                    target_destinations.append(rec.destination)
                if rec.destination_original and rec.destination_original not in target_destinations:
                    target_destinations.append(rec.destination_original)

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
                    SAVINGS_CATEGORY_TYPE: {'is_income': False, 'is_expense': False, 'is_saving': True, 'is_payment': False},
                    EXPENSE_CATEGORY_TYPE: {'is_income': False, 'is_expense': True, 'is_saving': False, 'is_payment': False},
                    PAYMENT_CATEGORY_TYPE: {'is_income': False, 'is_expense': False, 'is_saving': False, 'is_payment': True},
                }
                has_explicit_flags = any(k in request_data for k in ['is_expense', 'is_payment', 'is_income', 'is_saving'])
                if has_explicit_flags:
                    if 'is_income' in request_data and request_data['is_income'] is not None:
                        update_params['is_income'] = bool(request_data['is_income'])
                    if 'is_expense' in request_data and request_data['is_expense'] is not None:
                        update_params['is_expense'] = bool(request_data['is_expense'])
                    if 'is_saving' in request_data and request_data['is_saving'] is not None:
                        update_params['is_saving'] = bool(request_data['is_saving'])
                    if 'is_payment' in request_data and request_data['is_payment'] is not None:
                        update_params['is_payment'] = bool(request_data['is_payment'])
                elif category_type == PAYMENT_CATEGORY_TYPE:
                    # Direct bank expenses (e.g. Rent, Legal Fees, Car Loan, ATM Cash Withdrawals):
                    # If category is an Expense category or payee is ATM withdrawal, it is BOTH a payment AND a living expense.
                    cat_obj = TransactionCategory.objects.filter(id=category).first() if category else None
                    dest_str = (destination or '').lower()
                    is_atm = 'atm' in dest_str or '出金' in dest_str or '７ｂｋ' in dest_str or 'ゆうちょ' in dest_str
                    is_exp_cat = bool(cat_obj and (cat_obj.category_type == EXPENSE_CATEGORY_TYPE or cat_obj.category == 'Cash Payments'))
                    update_params.update({
                        'is_income': False,
                        'is_expense': is_atm or is_exp_cat,
                        'is_saving': False,
                        'is_payment': True,
                    })
                elif category_type in flag_mapping:
                    update_params.update(flag_mapping[category_type])

                Transaction.objects.filter(
                    Q(destination__in=target_destinations) | Q(destination_original__in=target_destinations),
                    is_deleted=False
                ).update(**update_params)

                # Safeguard: Bank account debits (outflows) must always have is_payment=True
                Transaction.objects.filter(
                    Q(destination__in=target_destinations) | Q(destination_original__in=target_destinations),
                    account__account_type='BANK_ACCOUNT',
                    is_income=False,
                    is_saving=False,
                    is_deleted=False
                ).update(is_payment=True)

                if merge_ids:
                    DestinationMap.objects.filter(id__in=merge_ids).delete()

            payee_details = self.get_payee_by_id_or_name({'id': payee_id}, include_transactions=False)
            return True, payee_details
        except Exception as e:
            logging.exception("An unexpected error occurred while updating payee: %s", e)
            return False, {'error': str(e)}

