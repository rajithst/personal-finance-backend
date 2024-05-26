import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.connector.card_loader import CardLoader
from transactions.models import ImportRules, Transaction, Income
from transactions.serializers.serializers import TransactionSerializer, IncomeSerializer


class TransactionImportView(APIView):
    def get(self, request):
        loader = CardLoader()
        expenses, incomes, import_rules = loader.process()
        try:
            expense_objects = []
            for expense in expenses.to_dict('records'):
                expense_objects.append(Transaction(**expense))
            Transaction.objects.bulk_create(expense_objects)
            logging.info('Expenses imported')

            income_objects = []
            valid_fields = [field.name for field in Income._meta.get_fields()]
            override_fields = {'category': 'category_id'}
            for override_field in override_fields.keys():
                if override_field in valid_fields:
                    valid_fields.remove(override_field)
                    valid_fields.append(override_fields[override_field])
            for income in incomes.to_dict('records'):
                income_data = {}
                for k in income.keys():
                    if k in valid_fields:
                        income_data[k] = income[k]
                income_objects.append(Income(**income_data))
            Income.objects.bulk_create(income_objects)

            for src in import_rules:
                last_import_date = import_rules[src]
                if last_import_date:
                    existing_rule = ImportRules.objects.filter(source=src).first()
                    if existing_rule:
                        existing_rule.last_import_date = last_import_date
                        existing_rule.save()
                    else:
                        ImportRules.objects.create(source_id=src, last_import_date=last_import_date)
            return Response("Successfully saved", status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(f'Failed to save data: {e}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
