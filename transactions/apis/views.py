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


class DashboardView(APIView):

    def get(self, request):
        year = request.query_params.get('year', 2024)
        dashboard_service = DashboardService()
        incomes = dashboard_service.get_monthly_transaction_summary('is_income', year)
        expenses = dashboard_service.get_monthly_transaction_summary('is_expense', year)
        payments = dashboard_service.get_monthly_transaction_summary('is_payment', year)
        savings = dashboard_service.get_monthly_transaction_summary('is_saving', year)
        category_wise_expenses = dashboard_service.get_monthly_transaction_category_summary('is_expense', year)
        account_wise_expenses = dashboard_service.get_account_wise_sum('is_expense', year)
        payment_by_destination = dashboard_service.get_monthly_payment_destination_wise_sum('is_payment', year)
        top_ten_expenses = dashboard_service.get_top_ten_expenses()
        return Response({"income": incomes, "payment_by_destination": payment_by_destination,
                         "account_wise_expenses": account_wise_expenses,
                         "category_wise_expenses": category_wise_expenses, "expense": expenses,
                         "top_ten_expenses": top_ten_expenses,
                         "payment": payments, "saving": savings})


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
