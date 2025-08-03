from rest_framework import serializers

from investments.portfolio.models import Portfolio, PortfolioDailyGrowth


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = '__all__'


class PortfolioDailyGrowthSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioDailyGrowth
        fields = '__all__'


class ResponsePortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['id', 'name', 'description', 'currency']
