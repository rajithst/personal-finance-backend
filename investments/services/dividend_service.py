import calendar
import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

from investments.connector.polygon_api import PolygonAPI
from investments.models import Holding, Company, DividendHistory, StockPurchaseHistory, DividendPayment, Portfolio
from investments.serializers.response_serializers import ResponseDividendPaymentSerializer
from investments.serializers.serializers import DividendHistorySerializer
from investments.validators.dividend_validator import DividendValidator
from investments.validators.portfolio_validator import PortfolioValidator

is_dev_env = settings.ENV == 'dev'
if not is_dev_env:
    try:
        from google.appengine.api import taskqueue
    except ImportError:
        logging.exception('Failed to import taskqueue from google.appengine.api')

DIVIDEND_TAX_RATE = 20.315


class DividendService:
    """
    A service class to handle dividend-related operations such as calculations,
    updates, imports, and income retrieval.

    Attributes:
        dividend_api (PolygonAPI): The API client for fetching dividend data.
    """

    def __init__(self, dividend_api=None):
        """
        Initializes the DividendService.

        Args:
            dividend_api (PolygonAPI, optional): The API client for fetching dividend data.
        """
        self.dividend_api = dividend_api or PolygonAPI()

    def calculate_dividend_payments(self, request_params):
        """
        Calculates and records dividend payments for holdings.

        Iterates through holdings, checks for eligible dividend payments, and
        records them in the DividendPayment model if not already recorded.

        Raises:
            Exception: Logs any error encountered during the calculation process.
        """
        from_date = request_params.get('from_date')
        portfolio_id = request_params.get('portfolio')
        if not from_date:
            from_date = date.today().strftime('%Y-%m-%d')

        portfolio_users = Portfolio.cron_objects.only('id', 'user_id')
        if portfolio_id:
            portfolio_users = portfolio_users.filter(id=portfolio_id)

        for portfolio_user in portfolio_users:
            user_id = portfolio_user.user_id
            portfolio_id = portfolio_user.id
            holding_companies = Holding.cron_objects.select_related('company').filter(portfolio_id=portfolio_id,
                                                                                      user_id=user_id).values_list(
                'company_id', flat=True).distinct()
            try:
                for company in holding_companies:
                    dividend_payments = DividendHistory.objects.filter(company_id=company, payment_date__gte=from_date)
                    for dividend_payer in dividend_payments:
                        ex_dividend_date = dividend_payer.ex_dividend_date
                        purchased_shares = (StockPurchaseHistory.cron_objects
                                            .filter(company_id=company,
                                                    portfolio_id=portfolio_id,
                                                    user_id=user_id,
                                                    purchase_date__lt=ex_dividend_date)
                                            .aggregate(total_shares=Sum('quantity'))
                                            .get('total_shares', 0)
                                            )

                        DividendPayment.cron_objects.update_or_create(
                            company_id=company,
                            ex_dividend_date=ex_dividend_date,
                            payment_date=dividend_payer.payment_date,
                            portfolio_id=portfolio_id,
                            user_id=user_id,
                            defaults={
                                'amount': dividend_payer.amount,
                                'quantity': purchased_shares or 0,
                            }
                        )
                return True
            except Exception as e:
                logging.exception(f'Failed to calculate dividend payments. {e}')
                return False

    def update_dividend_history(self, request_params):

        DividendValidator.validate_request(request_params)
        from_date = request_params.get('from_date') or date.today().strftime('%Y-%m-%d')
        to_date = request_params.get('to_date') or (date.today() + relativedelta(days=+5)).strftime('%Y-%m-%d')
        company = request_params.get('company')

        dividends = self.dividend_api.get_dividend_calendar(company, from_date, to_date)
        dividend_objects = []
        for dividend in dividends:
            dividend, _ = DividendHistory.objects.update_or_create(
                company_id=company,
                payment_date=dividend['payment_date'],
                defaults={
                    'amount': dividend['amount'],
                    'ex_dividend_date': dividend['ex_dividend_date'],
                }
            )
            dividend_objects.append(dividend)
        return DividendHistorySerializer(dividend_objects, many=True).data

    def enqueue_dividend_refresh_tasks(self):
        """
        Imports dividend data for all companies in the database.

        Raises:
            EnvironmentError: If the method is called in a development environment
            or if no companies are found in the database.
        """
        is_dev_env = settings.ENV == 'dev'
        companies = Company.objects.values_list('symbol', flat=True).distinct()
        if not companies:
            raise EnvironmentError('Cannot import dividends from empty company list. Please insert a company list')

        from_date = date.today().strftime('%Y-%m-%d')
        to_date = (date.today() + relativedelta(days=+5)).strftime('%Y-%m-%d')
        if is_dev_env:
            for company in companies[:5]:
                self.update_dividend_history({'company': company, 'from_date': from_date, 'to_date': to_date})
                self.calculate_dividend_payments({'company': company, 'from_date': from_date})

        else:
            for company in companies:
                taskqueue.add(
                    name='sync-dividends',
                    url='/investments/dividends/cron/income/daily',
                    target='coincraftservice',
                    params={'company': company, 'from_date': from_date, 'to_date': to_date})

    def get_dividend_income(self, request_params):
        PortfolioValidator.validate_request(request_params)
        dividend_portfolio = Portfolio.objects.get(id=request_params.get('portfolio'))
        dividends_by_month = DividendPayment.objects.filter(portfolio_id=request_params.get('portfolio')).annotate(
            year_month=TruncMonth('payment_date')
        ).values('year_month').annotate(
            total_amount=Sum(F('quantity') * F('amount'))
        ).order_by('year_month')
        dividends_by_month_with_records = []
        for month_data in dividends_by_month:
            year_month = month_data['year_month']
            total_amount = month_data['total_amount']
            records_for_month = DividendPayment.objects.filter(
                payment_date__year=year_month.year,
                payment_date__month=year_month.month
            )
            serializer = ResponseDividendPaymentSerializer(records_for_month, many=True)
            dividends_by_month_with_records.append({'year': year_month.year, 'month': year_month.month,
                                                    'month_text': calendar.month_name[year_month.month],
                                                    'currency': dividend_portfolio.currency,
                                                    'total': total_amount, 'dividends': serializer.data})
        return dividends_by_month_with_records
