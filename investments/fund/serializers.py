from rest_framework import serializers

from investments.fund.models import Fund, FundDailyPrice, FundPurchaseHistory


class IndexFundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fund
        fields = '__all__'


class IndexFundDailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundDailyPrice
        fields = '__all__'


class IndexFundPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FundPurchaseHistory
        fields = '__all__'
