from rest_framework import serializers

from investments.models import StockPurchaseHistory, Company, Holding, \
    StockDailyPrice, Forex, CompanyIndustry, CompanySector, Portfolio, IndexFund, IndexFundDailyPrice, \
    IndexFundPurchaseHistory, DividendPayment, DividendHistory, PortfolioDailyGrowth


class CompanyIndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyIndustry
        fields = '__all__'


class CompanySectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySector
        fields = '__all__'


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class StockPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPurchaseHistory
        fields = '__all__'


class IndexFundSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexFund
        fields = '__all__'


class PortfolioDailyGrowthSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioDailyGrowth
        fields = '__all__'


class HoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = '__all__'


class DividendHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendHistory
        fields = '__all__'


class DividendPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendPayment
        fields = '__all__'


class StockDailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDailyPrice
        fields = '__all__'


class IndexFundDailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexFundDailyPrice
        fields = '__all__'


class IndexFundPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexFundPurchaseHistory
        fields = '__all__'


class ForexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forex
        fields = '__all__'
