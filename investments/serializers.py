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
                  'profit_loss', 'price_updated_at', 'profit_change_percentage', 'company', 'company_name', 'image']

    profit_change_percentage = serializers.SerializerMethodField(method_name='get_profit_change_percentage')
    company_name = serializers.ReadOnlyField(source='company.company_name')
    image = serializers.ReadOnlyField(source='company.image')

    def get_profit_change_percentage(self, obj):
        return (obj.profit_loss / obj.total_investment) * 100


class DividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = '__all__'
