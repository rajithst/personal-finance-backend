import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Sum

from investments.connector.polygon_api import PolygonAPI
from investments.models import Holding, Company, DividendHistory, StockPurchaseHistory, DividendPayment
# from google.appengine.api import taskqueue

from investments.serializers.response_serializers import ResponseDividendPaymentSerializer

DIVIDEND_TAX_RATE = 20.315


class DividendService:

    def calculate_dividend_payments(self):
        today = date.today().strftime('%Y-%m-%d')
        holding_companies = Holding.objects.select_related('company').values_list('company_id', flat=True).distinct()
        try:
            for company in holding_companies:
                dividend_payer = DividendHistory.objects.filter(company_id=company, payment_date_gte=today)
                if dividend_payer:
                    dividend_payer = dividend_payer[0]
                    ex_dividend_date = dividend_payer.ex_dividend_date
                    purchased_shares = StockPurchaseHistory.objects.filter(company_id=company,
                                                                           purchase_date__lt=ex_dividend_date).annotate(
                        shares=Sum('quantity')).values('shares')
                    dividend_payment = DividendPayment.objects.filter(company_id=company,
                                                                      payment_date=dividend_payer.payment_date)
                    if not dividend_payment.exists():
                        DividendPayment.objects.create(
                            company_id=company,
                            amount=dividend_payer.amount,
                            pre_tax_amount=dividend_payer.amount,
                            quantity=purchased_shares,
                            payment_date=dividend_payer.payment_date,
                            payment_received=False,
                        )
                    else:
                        dividend_payment.update(amount=dividend_payer.amount, quantity=purchased_shares)
        except Exception as e:
            logging.exception('Failed to calculate dividend payments ')

    def update_dividends(self, ticker, from_date, to_date):
        client = PolygonAPI()
        if not from_date:
            from_date = date.today().strftime('%Y-%m-%d')
        if not to_date:
            to_date = date.today() + relativedelta(days=+5)
            to_date = to_date.strftime('%Y-%m-%d')
        current_year = date.today().year
        dividends = client.get_dividend_calendar(ticker, from_date, to_date)
        for dividend in dividends:
            payment_date = dividend['payment_date']
            queryset = DividendHistory.objects.filter(company_id=ticker, payment_date__year=current_year,
                                                      payment_date=payment_date)
            if not queryset.exists():
                DividendHistory.objects.create(
                    company_id=ticker,
                    amount=dividend['amount'],
                    ex_dividend_date=dividend['ex_dividend_date'],
                    payment_date=payment_date,

                )
            else:
                queryset.update(amount=dividend['amount'])

    def import_dividends(self):
        is_dev_env = settings.ENV == 'dev'
        if is_dev_env:
            raise EnvironmentError('Cannot import dividends from dev environment')
        companies = Company.objects.values_list('symbol', flat=True).distinct()
        if not companies:
            raise EnvironmentError('Cannot import dividends from empty company list. Please insert a company list')
        for company in companies:
            pass
            # taskqueue.add(
            #     name='future-dividends',
            #     url='/investments/dividends/daily',
            #     target='worker',
            #     params={'company': company})

    def get_dividend_income(self):
        dividends = DividendPayment.objects.all()
        serializer = ResponseDividendPaymentSerializer(dividends, many=True)
        return serializer.data

