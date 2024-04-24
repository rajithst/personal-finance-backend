from rest_framework import serializers

from investments.models import StockPurchaseHistory, Company, IndexFundPurchaseHistory, Dividend


class StockPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPurchaseHistory
        fields = ['id', 'purchase_date', 'company', 'quantity', 'purchase_price']


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class IndexFundPurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexFundPurchaseHistory
        fields = '__all__'


class DividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = '__all__'
