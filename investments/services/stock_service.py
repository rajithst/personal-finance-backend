import logging
import time
from datetime import date

from django.db import transaction, IntegrityError

from investments.connector.market_api import MarketApi
from investments.models import StockDailyPrice, Company, StockSplit
from investments.serializers.serializers import StockDailyPriceSerializer
from investments.validators.stock_validator import TickerValidator, BulkTickerValidator

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self, market_api=None):
        self.market_api = market_api or MarketApi()

    def update_daily_price(self, request_data):
        try:
            companies = request_data.get('companies', '')
            if not companies:
                companies = Company.objects.values_list('symbol', flat=True)
            else:
                companies = companies.split(',')

            daily_data = self.market_api.get_day_snapshot(tickers=companies)
        except Exception as e:
            logging.error(f"Error fetching market data: {e}")
            raise ValueError("Failed to fetch market data.")
        existing_entries = {entry.company_id: entry for entry in StockDailyPrice.objects.filter(
            company_id__in=[data['company_id'] for data in daily_data],
            date__in=[data.get('date') for data in daily_data]
        )}
        new_entries = []
        for data in daily_data:
            entry = existing_entries.get(data['company_id'])
            if entry:
                entry.current_price = data.get('current_price')
                entry.change_percentage = data.get('change_percentage')
                entry.change = data.get('change')
                entry.day_high_price = data.get('day_high_price')
                entry.day_low_price = data.get('day_low_price')
                entry.save()
            else:
                price_object = self.create_stock_daily_price_object(data)
                new_entries.append(price_object)
        if new_entries:
            with transaction.atomic():
                StockDailyPrice.cron_objects.bulk_create(new_entries)

    def get_price_history(self, request_data):
        TickerValidator.validate(request_data)
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        company = request_data.get('company')
        today = date.today()
        if not start_date and not end_date:
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)

        queryset = StockDailyPrice.cron_objects.filter(company_id=company, date__range=(start_date, end_date)).order_by(
            'date')
        serializer = StockDailyPriceSerializer(queryset, many=True)
        return serializer.data

    def sync_historical_data(self, request_data):
        BulkTickerValidator.validate(request_data)

        from_date = request_data.get('from_date', None)
        to_date = request_data.get('to_date', None)
        companies = request_data.get('companies')
        companies = companies.split(',')

        def chunk_list(lst, chunk_size):
            for i in range(0, len(lst), chunk_size):
                yield lst[i:i + chunk_size]
        try:
            for batch in chunk_list(companies, 10):
                historical_data = self.market_api.get_historical_data(batch, from_date=from_date, to_date=to_date)
                new_entries = []
                for data in historical_data:
                    price_object = self.create_stock_daily_price_object(data)
                    new_entries.append(price_object)
                if new_entries:
                    with transaction.atomic():
                        StockDailyPrice.cron_objects.bulk_create(new_entries)
                time.sleep(10)
            return True
        except Exception as e:
            logging.exception(f"Error fetching historical data: {e}")
            raise ValueError("Failed to fetch historical data.")

    def create_stock_daily_price_object(self, data):
        return StockDailyPrice(
            company_id=data['company_id'],
            date=data['date'],
            current_price=data['current_price'],
            change_percentage=data['change_percentage'],
            change=data['change'],
            day_high_price=data['day_high_price'],
            day_low_price=data['day_low_price'],

        )

    def update_daily_stock_split(self, request_data):
        try:
            companies = request_data.get('companies', '')
            if not companies:
                companies = list(Company.objects.values_list('symbol', flat=True))
            else:
                companies = companies.split(',')
            splits = self.market_api.get_historical_stock_splits(companies)
            for split in splits:
                try:
                    StockSplit.cron_objects.update_or_create(
                        company_id=split['symbol'],
                        split_date=split['date'],
                        defaults={
                            'split_ratio': f"{split['denominator']}:{split['numerator']}",
                        }
                    )
                except IntegrityError as e:
                    logging.exception(f"Error inserting or updating split data: {e}")

            return splits

        except Exception as e:
            logging.exception(f"Error fetching stock split data: {e}")
            return None

