import calendar

from rest_framework import serializers

from investments.dividend.models import DividendPayment, DividendHistory

COMPANY_NAME_SOURCE = 'company.company_name'
COMPANY_INDUSTRY_SOURCE = 'company.industry.name'
COMPANY_SECTOR_SOURCE = 'company.sector.name'
COMPANY_IMAGE_SOURCE = 'company.image'


class DividendHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendHistory
        fields = '__all__'


class DividendPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendPayment
        fields = '__all__'


class ResponseDividendPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendPayment
        fields = ['id', 'company', 'amount', 'quantity', 'payment_date', 'payment_received', 'company_name',
                  'industry', 'sector', 'ex_dividend_date', 'image', 'stock_currency', 'year', 'month', 'month_text']

    company_name = serializers.ReadOnlyField(source=COMPANY_NAME_SOURCE)
    image = serializers.ReadOnlyField(source=COMPANY_IMAGE_SOURCE)
    industry = serializers.ReadOnlyField(source=COMPANY_INDUSTRY_SOURCE)
    sector = serializers.ReadOnlyField(source=COMPANY_SECTOR_SOURCE)
    stock_currency = serializers.SerializerMethodField(method_name='get_stock_currency')
    year = serializers.SerializerMethodField(method_name='get_year')
    month = serializers.SerializerMethodField(method_name='get_month')
    month_text = serializers.SerializerMethodField(method_name='get_month_text')

    def get_year(self, data):
        return data.payment_date.year

    def get_month(self, data):
        return data.payment_date.month

    def get_month_text(self, data):
        return calendar.month_name[data.payment_date.month]

    def get_stock_currency(self, data):
        if data.company.currency == 'USD':
            return '$'
        elif data.company.currency == 'JPY':
            return '¥'
        else:
            return ''
