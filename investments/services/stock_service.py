import logging
from datetime import date

from django.db import transaction

from investments.connector.market_api import MarketApi
from investments.models import StockDailyPrice
from investments.serializers.serializers import StockDailyPriceSerializer

logger = logging.getLogger(__name__)


class StockService:
    """
    Service class for managing stock data. This includes updating daily stock prices,
    retrieving price history, and syncing historical stock data.

    Attributes:
        market_api (MarketApi): An instance of the MarketApi for fetching stock data.
    """
    def __init__(self, market_api=None):
        """
        Initializes the StockService with a provided or default MarketApi instance.

        Args:
            market_api (MarketApi, optional): A custom MarketApi instance for fetching stock data.
                Defaults to None, in which case a new MarketApi instance is created.
        """
        self.market_api = market_api or MarketApi()

    def update_daily_price(self, companies):
        """
        Updates daily stock prices for a list of companies.

        Args:
            companies (list): List of company symbols for which to update daily prices.

        Raises:
            ValueError: If no company symbols are provided or if market data fetching fails.
        """
        logging.info('fetching market data..')
        if not companies:
            raise ValueError('No symbols provided')
        try:
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
                price_object = self.extract_new_price_object(data)
                new_entries.append(price_object)
        if new_entries:
            with transaction.atomic():
                serializer = StockDailyPriceSerializer(data=new_entries, many=True)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

    def get_price_history(self, company, start_date=None, end_date=None):
        """
        Retrieves the price history for a specific company within a date range.

        Args:
            company (str): The symbol of the company.
            start_date (datetime.date, optional): The start date of the range. Defaults to January 1 of the current year.
            end_date (datetime.date, optional): The end date of the range. Defaults to December 31 of the current year.

        Returns:
            list: Serialized price history data for the specified company and date range.
        """
        today = date.today()
        if not start_date and not end_date:
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)

        queryset = StockDailyPrice.objects.filter(company_id=company, date__range=(start_date, end_date)).order_by(
            'date')
        serializer = StockDailyPriceSerializer(queryset, many=True)
        return serializer.data

    def sync_historical_data(self, request_data):
        """
        Syncs historical stock price data for a list of tickers.

        Args:
            request_data (dict): Contains the tickers and optional date range for syncing:
                - tickers (list): List of company symbols to fetch data for.
                - from_date (str, optional): Start date of the range (YYYY-MM-DD).
                - to_date (str, optional): End date of the range (YYYY-MM-DD).

        Returns:
            bool: True if successful, otherwise raises an exception.
        """
        tickers = request_data.get('tickers')
        from_date = request_data.get('from_date', None)
        to_date = request_data.get('to_date', None)
        if not tickers:
            raise ValueError("Tickers are required for syncing historical data.")
        historical_data = self.market_api.get_historical_data(tickers, from_date=from_date, to_date=to_date)
        new_entries = []
        for data in historical_data:
            price_object = self.extract_new_price_object(data)
            new_entries.append(price_object)
        if new_entries:
            with transaction.atomic():
                serializer = StockDailyPriceSerializer(data=new_entries, many=True)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

    def extract_new_price_object(self, data):
        """
        Extracts a new stock price object from raw data.

        Args:
            data (dict): Raw data from the market API.

        Returns:
            dict: A formatted stock price object ready for database insertion.
        """
        price_object = {
            'date': data.get('date'),
            'change_percentage': data.get('change_percentage'),
            'change': data.get('change'),
            'current_price': data.get('current_price'),
            'day_high_price': data.get('day_high_price'),
            'day_low_price': data.get('day_low_price'),
            'company_id': data['company_id'],
        }
        return price_object
