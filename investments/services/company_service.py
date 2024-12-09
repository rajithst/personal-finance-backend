import logging
import time

from django.db import transaction
from requests import RequestException

from investments.connector.market_api import MarketApi
from investments.models import CompanySector, CompanyIndustry
from investments.serializers.serializers import CompanySerializer

logger = logging.getLogger(__name__)


class CompanyService:
    """
    A service class to handle company data import and processing.

    Attributes:
        market_api (MarketApi): The API connector for fetching market data.
    """
    def __init__(self, market_api=None):
        """
        Initializes the CompanyService with a market API connector.

        Args:
            market_api (MarketApi, optional): The market API connector. Defaults to a new MarketApi instance.
        """
        self.market_api = market_api or MarketApi()

    def import_company_information(self, request_data):
        """
        Imports and processes company information from external API.

        Args:
            request_data (dict): Request payload containing company tickers.

        Returns:
            tuple: A boolean indicating success, and the response data or errors.

        Raises:
            ValueError: If no tickers are provided in the request data.
        """
        companies = request_data.get('tickers')
        if not companies:
            logger.error("No tickers provided.")
            raise ValueError("Tickers are required.")
        company_data = self.get_company_data(companies)

        sectors = {s.name: s.id for s in CompanySector.objects.all()}
        industries = {i.name: i.id for i in CompanyIndustry.objects.all()}
        skipped_companies = []
        company_objects = []
        for data in company_data:
            sector_id = sectors.get(data.get('sector'))
            industry_id = industries.get(data.get('industry'))
            if not sector_id or not industry_id:
                logger.warning(f"Skipping {data.get('ticker')} due to missing sector or industry.")
                skipped_companies.append(data.get('ticker'))
                continue
            data['sector'] = sector_id
            data['industry'] = industry_id
            company_objects.append(data)
        return self.bulk_create_company(company_objects)

    def bulk_create_company(self, company_data):
        """
        Bulk creates company records in the database.

        Args:
            company_data (list): List of company data dictionaries.

        Returns:
            tuple: A boolean indicating success, and the response data or errors.
        """
        with transaction.atomic():
            serializer = CompanySerializer(data=company_data, many=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return True, serializer.data
            return False, serializer.errors

    def get_company_data(self, companies):
        """
        Fetches company data from the market API with retry logic.

        Args:
            companies (list): List of company tickers.

        Returns:
            list: A list of company data dictionaries.

        Raises:
            ValueError: If no tickers are provided.
            Exception: If the API fails after all retry attempts.
        """
        if not companies:
            logger.error("No tickers provided.")
            raise ValueError("Tickers are required.")

        logger.info(f"Fetching data for tickers: {companies}")
        for attempt in range(3):
            try:
                company_data = self.market_api.get_company_data(companies)
                return company_data
            except RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)
        logger.error("Failed to fetch company data after 3 retries.")
        raise Exception("Failed to fetch company data after 3 retries.")
