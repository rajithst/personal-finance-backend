from rest_framework import serializers

from investments.stock.models import Holding, StockPurchaseHistory, StockDailyPrice

COMPANY_NAME_SOURCE = 'company.company_name'
COMPANY_INDUSTRY_SOURCE = 'company.industry.name'
COMPANY_SECTOR_SOURCE = 'company.sector.name'
COMPANY_IMAGE_SOURCE = 'company.image'


class StockPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPurchaseHistory
        fields = '__all__'


class HoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = '__all__'


class StockDailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDailyPrice
        fields = '__all__'


class ResponseHoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = ['id', 'quantity', 'average_price', 'current_price', 'total_investment', 'current_value',
                  'stock_currency', 'industry', 'sector',
                  'profit_loss', 'price_updated_at', 'profit_change_percentage', 'company', 'company_name', 'image']

    profit_change_percentage = serializers.SerializerMethodField(method_name='get_profit_change_percentage')
    company_name = serializers.ReadOnlyField(source=COMPANY_NAME_SOURCE)
    industry = serializers.ReadOnlyField(source=COMPANY_INDUSTRY_SOURCE)
    sector = serializers.ReadOnlyField(source=COMPANY_SECTOR_SOURCE)
    image = serializers.ReadOnlyField(source=COMPANY_IMAGE_SOURCE)

    def get_profit_change_percentage(self, obj):
        return (obj.profit_loss / obj.total_investment) * 100


class ResponseStockPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPurchaseHistory
        fields = ['id', 'purchase_date', 'year', 'month', 'quantity', 'purchase_price', 'stock_currency',
                  'exchange_rate', 'company',
                  'company_name', 'industry', 'sector', 'image']

    image = serializers.ReadOnlyField(source=COMPANY_IMAGE_SOURCE)
    company_name = serializers.ReadOnlyField(source=COMPANY_NAME_SOURCE)
    industry = serializers.ReadOnlyField(source=COMPANY_INDUSTRY_SOURCE)
    sector = serializers.ReadOnlyField(source=COMPANY_SECTOR_SOURCE)
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


class ResponseStockPriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDailyPrice
        fields = ['id', 'date', 'current_price', 'change_percentage', 'change', 'day_high_price', 'day_low_price',
                  'company', 'company_name', 'industry', 'sector', 'image']

    image = serializers.ReadOnlyField(source=COMPANY_IMAGE_SOURCE)
    company_name = serializers.ReadOnlyField(source=COMPANY_NAME_SOURCE)
    industry = serializers.ReadOnlyField(source=COMPANY_INDUSTRY_SOURCE)
    sector = serializers.ReadOnlyField(source=COMPANY_SECTOR_SOURCE)
