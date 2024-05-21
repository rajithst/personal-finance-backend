import calendar

from rest_framework import serializers

from investments.models import StockPurchaseHistory, Company, IndexFundPurchaseHistory, Dividend, Holding, \
    StockDailyPrice


class StockPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPurchaseHistory
        fields = '__all__'


class StockDailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDailyPrice
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class IndexFundPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexFundPurchaseHistory
        fields = '__all__'


class HoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = ['id', 'quantity', 'average_price', 'current_price', 'total_investment', 'current_value',
                  'stock_currency',
                  'profit_loss', 'price_updated_at', 'profit_change_percentage', 'company', 'company_name', 'image']

    profit_change_percentage = serializers.SerializerMethodField(method_name='get_profit_change_percentage')
    company_name = serializers.ReadOnlyField(source='company.company_name')
    image = serializers.ReadOnlyField(source='company.image')

    def get_profit_change_percentage(self, obj):
        return (obj.profit_loss / obj.total_investment) * 100


class DividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = ['id', 'company', 'amount', 'ex_dividend_date', 'payment_date', 'payment_received', 'company_name',
                  'image', 'stock_currency', 'year', 'month', 'month_text']

    company_name = serializers.ReadOnlyField(source='company.company_name')
    image = serializers.ReadOnlyField(source='company.image')
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
        fields = ['id', 'purchase_date', 'quantity', 'purchase_price', 'stock_currency', 'exchange_rate', 'company',
                  'company_name',
                  'image']

    company_name = serializers.ReadOnlyField(source='company.company_name')
    image = serializers.ReadOnlyField(source='company.image')
    stock_currency = serializers.SerializerMethodField(method_name='get_stock_currency')

    def get_stock_currency(self, data):
        if data.company.currency == 'USD':
            return '$'
        elif data.company.currency == 'JPY':
            return '¥'
        else:
            return ''
