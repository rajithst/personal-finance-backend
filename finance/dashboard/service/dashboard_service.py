from datetime import datetime, timedelta

from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from finance.transactions.models import Transaction


class DashboardService:

    def get_queryset(self):
        return Transaction.objects.filter(is_deleted=False)

    def get_monthly_kpi_summary(self, year):
        """
        Calculates income, expense, payment, and savings aggregated by month in a single SQL query.
        """
        if not year:
            raise ValueError('Required filter year')

        queryset = (self.get_queryset().filter(date__year=year, is_deleted=False)
                    .annotate(month=TruncMonth('date'))
                    .values('month')
                    .annotate(
                        income=Sum('amount', filter=Q(is_income=True) & ~Q(category__category='Internal Transfer') & ~Q(category_id=19) & ~Q(is_third_party=True)),
                        expense=Sum('amount', filter=Q(is_expense=True, is_saving=False, is_third_party=False)),
                        payment=Sum('amount', filter=Q(is_payment=True) & ~Q(category__category='Internal Transfer') & ~Q(category_id=19)),
                        saving_out=Sum('amount', filter=Q(is_saving=True, is_payment=True)),
                        saving_in=Sum('amount', filter=Q(is_saving=True, is_income=True)),
                        transfer=Sum('amount', filter=Q(category__category='Internal Transfer') | Q(category_id=19)),
                    )
                    .order_by('month'))

        incomes, expenses, payments, savings, transfers = [], [], [], [], []
        for item in queryset:
            date = item['month']
            year_num, month_num = date.year, date.month
            incomes.append({'year': year_num, 'month': month_num, 'amount': item['income'] or 0})
            expenses.append({'year': year_num, 'month': month_num, 'amount': item['expense'] or 0})
            payments.append({'year': year_num, 'month': month_num, 'amount': item['payment'] or 0})
            net_saving = (item.get('saving_out') or item.get('saving') or 0) - (item.get('saving_in') or 0)
            savings.append({'year': year_num, 'month': month_num, 'amount': net_saving})
            transfers.append({'year': year_num, 'month': month_num, 'amount': item.get('transfer') or 0})

        return {
            'income': incomes,
            'expense': expenses,
            'payment': payments,
            'saving': savings,
            'transfer': transfers,
        }

    def get_income(self, year):
        return self.get_monthly_transaction_summary('is_income', year)

    def get_expense(self, year):
        return self.get_monthly_transaction_summary('is_expense', year)

    def get_payment(self, year):
        return self.get_monthly_transaction_summary('is_payment', year)

    def get_saving(self, year):
        return self.get_monthly_transaction_summary('is_saving', year)

    def get_monthly_expense_category_summary(self, year):
        return self.get_monthly_transaction_category_summary('is_expense', year)

    def get_monthly_expense_account_summary(self, year):
        return self.get_account_wise_sum('is_expense', year)

    def get_monthly_payment_account_summary(self, year):
        return self.get_account_wise_sum('is_payment', year)

    def get_monthly_payment_payee_summary(self, year):
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
        results = {}
        if not year:
            raise ValueError('Required filter year')

        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year})
                    .exclude(Q(category__category='Internal Transfer') | Q(category_id=19))
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'destination_original', 'destination')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )

        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append(
                {'destination_original': item['destination_original'], 'destination': item['destination'],
                 'amount': item['total_amount']})
        return results

    def get_monthly_transaction_summary(self, transaction_type, year):
        """
        Get the monthly transaction summary.

        Args:
            transaction_type (str): The transaction type.
            year (int): The year.

        Returns:
            list: The monthly transaction summary.
        """
        if not year:
            raise ValueError('Required filter year')

        if transaction_type == 'is_saving':
            queryset = (self.get_queryset().filter(is_saving=True, date__year=year, is_deleted=False)
                        .annotate(month=TruncMonth('date'))
                        .values('month')
                        .annotate(
                            outflow=Sum('amount', filter=Q(is_payment=True)),
                            inflow=Sum('amount', filter=Q(is_income=True)),
                        )
                        .order_by('month'))
            results = []
            for item in queryset:
                date = item['month']
                net_amount = (item['outflow'] or 0) - (item['inflow'] or 0)
                results.append({'year': date.year, 'month': date.month, 'amount': net_amount})
            return results

        filter_kwargs = {transaction_type: True, 'date__year': year, 'is_deleted': False}
        if transaction_type == 'is_expense':
            filter_kwargs['is_saving'] = False

        qs = self.get_queryset().filter(**filter_kwargs)
        if transaction_type in ['is_income', 'is_payment']:
            qs = qs.exclude(Q(category__category='Internal Transfer') | Q(category_id=19))

        queryset = (qs.annotate(month=TruncMonth('date'))
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
        if not year:
            raise ValueError('Required filter year')

        filter_kwargs = {transaction_type: True, 'date__year': year, 'is_deleted': False}
        if transaction_type == 'is_expense':
            filter_kwargs['is_saving'] = False

        queryset = (self.get_queryset().filter(**filter_kwargs)
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
        if not year:
            raise ValueError('Required filter year')
        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year})
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'account_id')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append({'category_id': item['account_id'], 'amount': item['total_amount']})
        return results

    def get_top_ten_expenses(self, year=None):
        """
        Get the top ten expenses.
        If year is provided, aggregates by destination with Sum and Count for that year.
        If year is None, preserves legacy last-month individual transaction query for backwards compatibility.

        Returns:
            list: The top ten expenses.
        """
        if not year:
            now = timezone.now().date() if hasattr(timezone, 'now') else datetime.today().date()
            first_day_this_month = now.replace(day=1)
            last_day_of_last_month = first_day_this_month - timedelta(days=1)
            first_day_of_last_month = last_day_of_last_month.replace(day=1)

            queryset = (self.get_queryset().filter(
                is_expense=True,
                is_income=False,
                is_payment=False,
                is_saving=False,
                date__gte=first_day_of_last_month,
                date__lte=last_day_of_last_month
            )).values('destination', 'destination_original', 'amount').order_by('-amount')[:10]
            results = []
            for item in queryset:
                results.append({'destination': item['destination'], 'destination_original': item['destination_original'],
                                'amount': item['amount']})
            return results

        queryset = (self.get_queryset().filter(
            is_expense=True,
            is_saving=False,
            date__year=year,
            is_deleted=False
        ).values('destination')
         .annotate(amount=Sum('amount'), count=Count('id'))
         .order_by('-amount')[:10])

        results = []
        for item in queryset:
            results.append({
                'destination': item['destination'],
                'destination_original': item['destination'],
                'amount': item['amount'],
                'count': item['count']
            })
        return results

    def get_top_ten_expenses_latest_month(self, year):
        """
        Get top ten aggregated expenses for the latest active month of the given year.
        """
        if not year:
            return {'month': None, 'month_name': '', 'items': []}

        latest_txn = self.get_queryset().filter(
            is_expense=True,
            is_saving=False,
            date__year=year,
            is_deleted=False
        ).order_by('-date').first()

        if not latest_txn:
            return {'month': None, 'month_name': '', 'items': []}

        latest_month = latest_txn.date.month
        month_name = latest_txn.date.strftime('%B')

        queryset = (self.get_queryset().filter(
            is_expense=True,
            is_saving=False,
            date__year=year,
            date__month=latest_month,
            is_deleted=False
        ).values('destination')
         .annotate(amount=Sum('amount'), count=Count('id'))
         .order_by('-amount')[:10])

        results = []
        for item in queryset:
            results.append({
                'destination': item['destination'],
                'destination_original': item['destination'],
                'amount': item['amount'],
                'count': item['count']
            })

        return {
            'month': latest_month,
            'month_name': month_name,
            'items': results
        }

