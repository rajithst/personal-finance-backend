from datetime import datetime, timedelta

from django.db.models import Sum
from django.db.models.functions import TruncMonth

from transactions.models import Transaction
from transactions.validators.dashboard_validator import DashboardValidator


class DashboardService:

    def __init__(self, year):
        self.year = year
    def get_queryset(self):
        return Transaction.objects.select_related('category', 'subcategory', 'account').filter(is_deleted=False)

    def get_income(self, year=None):
        return self.get_monthly_transaction_summary('is_income', year)

    def get_expense(self, year=None):
        return self.get_monthly_transaction_summary('is_expense', year)

    def get_payment(self, year=None):
        return self.get_monthly_transaction_summary('is_payment', year)

    def get_saving(self, year=None):
        return self.get_monthly_transaction_summary('is_saving', year)

    def get_monthly_expense_category_summary(self, year=None):
        return self.get_monthly_transaction_category_summary('is_expense', year)

    def get_monthly_payment_account_summary(self, year=None):
        return self.get_account_wise_sum('is_payment', year)

    def get_monthly_payment_payee_summary(self, year=None):
        return self.get_monthly_payment_destination_wise_sum('is_payment', year)
    def get_monthly_payment_destination_wise_sum(self, transaction_type, year):
        """
        Get the monthly payment destination wise sum.

        Args:
            transaction_type (str): The transaction type.
            year (int): The year.

        Returns:
            dict: The monthly payment destination wise sum.
        """
        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year})
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'destination_original', 'destination')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append(
                {'destination_original': item['destination_original'], 'destination': item['destination'],
                 'amount': item['total_amount']})
        return results


    def get_monthly_transaction_summary(self, transaction_type, year=None):
        """
        Get the monthly transaction summary.

        Args:
            transaction_type (str): The transaction type.
            year (int): The year.

        Returns:
            list: The monthly transaction summary.
        """
        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year or self.year}, is_deleted=False)
                    .annotate(month=TruncMonth('date'))
                    .values('month')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )
        results = []
        for item in queryset:
            date = item['month']
            results.append({'year': date.year, 'month': date.month, 'amount': item['total_amount']})
        return results

    def get_monthly_transaction_category_summary(self, transaction_type, year):
        """
        Get the monthly transaction category summary.

        Args:
            transaction_type (str): The transaction type.
            year (int): The year.

        Returns:
            dict: The monthly transaction category summary.
        """
        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year or self.year})
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'category_id')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month', 'category_id')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append({'category_id': item['category_id'], 'amount': item['total_amount']})
        return results

    def get_account_wise_sum(self, transaction_type, year):
        """
        Get the account wise sum.

        Args:
            transaction_type (str): The transaction type.
            year (int): The year.

        Returns:
            dict: The account wise sum.
        """
        queryset = self.get_queryset()
        queryset = (queryset.filter(
            **{transaction_type: True, 'date__year': year})
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'account_id')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )
        results = {}
        for item in queryset:
            print(item)
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append({'category_id': item['account_id'], 'amount': item['total_amount']})
        return results

    def get_top_ten_expenses(self):
        """
        Get the top ten expenses.

        Returns:
            list: The top ten expenses.
        """
        queryset = self.get_queryset()
        today = datetime.today()
        first_day_of_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_of_last_month = first_day_of_last_month.replace(day=1) + timedelta(days=31)
        last_day_of_last_month = last_day_of_last_month.replace(day=1) - timedelta(days=1)
        queryset = (queryset.filter(
            date__gte=first_day_of_last_month,
            date__lte=last_day_of_last_month
        )).values('destination', 'destination_original', 'amount').order_by('-amount')[:10]
        results = []
        for item in queryset:
            results.append({'destination': item['destination'], 'destination_original': item['destination_original'], 'amount': item['amount']})
        return results