import logging
import time

from django.db import transaction
from requests import RequestException

from investments.company.models import CompanySector, CompanyIndustry, Company
from investments.company.serializers import CompanySerializer, ResponseCompanySerializer
from investments.connector.market_api import MarketApi
from investments.validators.stock_validator import BulkTickerValidator

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, market_api=None):
        self.market_api = market_api or MarketApi()

    def fetch_company_info(self, request_data):
        BulkTickerValidator().validate(request_data)
        companies = request_data.get('companies')
        companies = list(set(companies.split(',')))
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
        with transaction.atomic():
            serializer = CompanySerializer(data=company_data, many=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return True, serializer.data
            return False, serializer.errors

    def get_company_data(self, companies):
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
        raise RuntimeError("Failed to fetch company data after 3 retries.")

    def get_company_list(self):
        companies = ResponseCompanySerializer(Company.cron_objects.select_related('sector', 'industry').all(),
                                              many=True)
        return companies.data
