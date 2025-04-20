from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.services.account_service import CreditAccountService
from transactions.services.dashboard_service import DashboardService
from transactions.services.settings_service import SettingsService
from transactions.validators.dashboard_validator import DashboardValidator


class DashboardView(APIView):

    def get(self, request):
        try:
            DashboardValidator.validate(request.query_params)
            year = request.query_params.get('year', None)
            dashboard_service = DashboardService()
            incomes = dashboard_service.get_income(year)
            expenses = dashboard_service.get_expense(year)
            payments = dashboard_service.get_payment(year)
            savings = dashboard_service.get_saving(year)
            category_wise_expenses = dashboard_service.get_monthly_expense_category_summary(year)
            account_wise_expenses = dashboard_service.get_monthly_payment_account_summary(year)
            payment_by_destination = dashboard_service.get_monthly_payment_payee_summary(year)
            top_ten_expenses = dashboard_service.get_top_ten_expenses()
            return Response({'data': {"income": incomes, "payment_by_destination": payment_by_destination,
                                      "account_wise_expenses": account_wise_expenses,
                                      "category_wise_expenses": category_wise_expenses, "expense": expenses,
                                      "top_ten_expenses": top_ten_expenses,
                                      "payment": payments, "saving": savings}, 'status': True, 'message': 'Success'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientSettingsView(APIView):

    def get(self, request):

        try:
            service = SettingsService()
            accounts = service.get_credit_accounts()
            transaction_categories = service.get_transaction_categories()
            transaction_subcategories = service.get_transaction_subcategories()
            account_types = service.get_account_types()
            account_providers = service.get_account_providers()
            return Response({'data': {
                'accounts': accounts,
                'account_types': account_types,
                'account_providers': account_providers,
                'transaction_categories': transaction_categories,
                'transaction_subcategories': transaction_subcategories
            }, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreditAccountView(APIView):

    def post(self, request):
        try:
            service = CreditAccountService()
            account = service.create_account(request.data)
            return Response({'data': account, 'status': True, 'message': 'Success'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            service = CreditAccountService()
            account = service.update_account(request.data)
            return Response({'data': account, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
