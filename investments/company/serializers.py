from rest_framework import serializers

from investments.company.models import CompanyIndustry, CompanySector, Company

COMPANY_NAME_SOURCE = 'company.company_name'
COMPANY_INDUSTRY_SOURCE = 'company.industry.name'
COMPANY_SECTOR_SOURCE = 'company.sector.name'
COMPANY_IMAGE_SOURCE = 'company.image'


class CompanyIndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyIndustry
        fields = '__all__'


class CompanySectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySector
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class ResponseCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['symbol', 'company_name', 'sector', 'industry', 'exchange', 'currency', 'stock_currency', 'country',
                  'website', 'image', 'description']

    stock_currency = serializers.SerializerMethodField(method_name='get_stock_currency')
    industry = serializers.ReadOnlyField(source=COMPANY_INDUSTRY_SOURCE)
    sector = serializers.ReadOnlyField(source=COMPANY_SECTOR_SOURCE)

    def get_stock_currency(self, data):
        if data.currency == 'USD':
            return '$'
        elif data.currency == 'JPY':
            return '¥'
        else:
            return ''
