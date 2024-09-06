import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.connector.card_loader import CardLoader
from transactions.models import ImportRules, Transaction


class TransactionImportView(APIView):
    def get(self, request):
        user = request.user
        loader = CardLoader(request_user_id=user.id)
        expenses, import_rules = loader.process()
        if expenses:
            try:
                expense_objects = []
                for expense in expenses:
                    expense_objects.append(Transaction(**expense))
                Transaction.objects.bulk_create(expense_objects)
                logging.info('Expenses imported')
            except Exception as e:
                logging.exception('Error importing Expenses objects')
        if import_rules:
            try:
                for src in import_rules:
                    last_import_date = import_rules[src]
                    if last_import_date:
                        existing_rule = ImportRules.objects.filter(source=src).first()
                        if existing_rule:
                            logging.info('existing_rule.last_import_date: {}'.format(existing_rule.last_import_date))
                            existing_rule.last_import_date = last_import_date.strftime('%Y-%m-%d')
                            existing_rule.save()
                        else:
                            ImportRules.objects.create(source_id=src,
                                                       last_import_date=last_import_date.strftime('%Y-%m-%d'))
            except Exception as e:
                logging.exception('Error importing imported rules')

        return Response("Successfully saved", status=status.HTTP_201_CREATED)
