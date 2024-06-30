import calendar

from investments.models import Holding, Dividend, StockPurchaseHistory, Company
from rest_framework import serializers


class ResponseHoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = ['id', 'quantity', 'average_price', 'current_price', 'total_investment', 'current_value',
                  'stock_currency', 'industry', 'sector',
                  'profit_loss', 'price_updated_at', 'profit_change_percentage', 'company', 'company_name', 'image']

    profit_change_percentage = serializers.SerializerMethodField(method_name='get_profit_change_percentage')
    company_name = serializers.ReadOnlyField(source='company.company_name')
    industry = serializers.ReadOnlyField(source='company.industry')
    sector = serializers.ReadOnlyField(source='company.sector')
    image = serializers.ReadOnlyField(source='company.image')

    def get_profit_change_percentage(self, obj):
        return (obj.profit_loss / obj.total_investment) * 100


class ResponseDividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = ['id', 'company', 'amount', 'ex_dividend_date', 'payment_date', 'payment_received', 'company_name',
                  'industry', 'sector', 'image', 'stock_currency', 'year', 'month', 'month_text']

    company_name = serializers.ReadOnlyField(source='company.company_name')
    image = serializers.ReadOnlyField(source='company.image')
    industry = serializers.ReadOnlyField(source='company.industry')
    sector = serializers.ReadOnlyField(source='company.sector')
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


class ResponseStockPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPurchaseHistory
        fields = ['id', 'purchase_date', 'year', 'month', 'quantity', 'purchase_price', 'stock_currency',
                  'exchange_rate', 'company',
                  'company_name', 'industry', 'sector', 'image']

    company_name = serializers.ReadOnlyField(source='company.company_name')
    image = serializers.ReadOnlyField(source='company.image')
    industry = serializers.ReadOnlyField(source='company.industry')
    sector = serializers.ReadOnlyField(source='company.sector')
    stock_currency = serializers.SerializerMethodField(method_name='get_stock_currency')
    year = serializers.SerializerMethodField(method_name='get_year')
    month = serializers.SerializerMethodField(method_name='get_month')

    def get_stock_currency(self, data):
        if data.company.currency == 'USD':
            return '$'
        elif data.company.currency == 'JPY':
            return '¥'
        else:
            return ''

    def get_year(self, data):
        return data.purchase_date.year

    def get_month(self, data):
        return data.purchase_date.month


class ResponseCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['symbol', 'company_name', 'sector', 'industry', 'exchange', 'currency', 'stock_currency', 'country',
                  'website',
                  'image', 'description']

    stock_currency = serializers.SerializerMethodField(method_name='get_stock_currency')
    def get_stock_currency(self, data):
        if data.currency == 'USD':
            return '$'
        elif data.currency == 'JPY':
            return '¥'
        else:
            return ''
