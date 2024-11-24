from investments.connector.market_api import MarketApi
from investments.serializers.serializers import CompanySerializer


class CompanyService:

    def get_company(self, request_data):
        companies = request_data.get('tickers')
        market_api = MarketApi()
        company_data = market_api.get_company_data(companies)
        company_serializer = CompanySerializer(data=company_data, many=True)
        if company_serializer.is_valid():
            company_serializer.save()
            return True, company_serializer.data
        return False, company_serializer.errors
