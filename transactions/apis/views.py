from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.models import Account, TransactionCategory, \
    TransactionSubCategory
from transactions.serializers.response_serializers import ResponseTransactionCategorySerializer, \
    ResponseTransactionSubCategorySerializer, \
    ResponseAccountSerializer
from transactions.serializers.serializers import AccountSerializer
from transactions.services.dashboard_service import DashboardService
from transactions.validators.dashboard_validator import DashboardValidator


class DashboardView(APIView):

    def get(self, request):
        try:
            DashboardValidator.validate(request.query_params)
            year = request.query_params.get('year', None)
            dashboard_service = DashboardService(year)
            incomes = dashboard_service.get_income()
            expenses = dashboard_service.get_expense()
            payments = dashboard_service.get_payment()
            savings = dashboard_service.get_saving()
            category_wise_expenses = dashboard_service.get_monthly_expense_category_summary()
            account_wise_expenses = dashboard_service.get_monthly_payment_account_summary()
            payment_by_destination = dashboard_service.get_monthly_payment_payee_summary()
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
        user_id = request.user.id
        accounts = Account.objects.filter(user_id=user_id).all()
        transaction_categories = TransactionCategory.objects.filter(user_id=user_id).all()
        transaction_subcategories = TransactionSubCategory.objects.filter(user_id=user_id).select_related(
            'category').all()
        transaction_category_serializer = ResponseTransactionCategorySerializer(transaction_categories, many=True)
        transaction_subcategories_serializer = ResponseTransactionSubCategorySerializer(transaction_subcategories,
                                                                                        many=True)
        accounts_serializer = ResponseAccountSerializer(accounts, many=True)
        return Response({'accounts': accounts_serializer.data,
                         'transaction_categories': transaction_category_serializer.data,
                         'transaction_sub_categories': transaction_subcategories_serializer.data})


class CreditAccountView(APIView):

    def post(self, request):
        data = request.data.copy()
        serializer = AccountSerializer(data=data)
        return self.handle_serializer(serializer)

    def put(self, request):
        data = request.data.copy()
        account = Account.objects.get(pk=data.get('id'))
        serializer = AccountSerializer(account, data=data, partial=True)
        return self.handle_serializer(serializer)

    def handle_serializer(self, serializer):
        if serializer.is_valid(raise_exception=True):
            saved_item = serializer.save()
            response_serializer = ResponseAccountSerializer(saved_item)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
