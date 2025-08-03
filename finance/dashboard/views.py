from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.dashboard.service.dashboard_service import DashboardService


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
        except ValidationError as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'year' not in params:
            errors['year'] = "Year is required."

        if errors:
            raise ValidationError(errors)
        return params
