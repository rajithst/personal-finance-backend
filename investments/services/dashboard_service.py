from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

from investments.models import StockPurchaseHistory, Holding, Portfolio
from investments.serializers.response_serializers import ResponsePortfolioSerializer


class PortfolioService:

    def get_portfolios(self):
        portfolios = Portfolio.objects.all()
        serializer = ResponsePortfolioSerializer(portfolios, many=True)
        return serializer.data


class DashboardService:

    def get_monthly_invested_amount(self, year):
        filter_params = {}
        if year:
            filter_params['purchase_date__year'] = year
        queryset = (StockPurchaseHistory.objects.select_related('company')
                    .filter(**filter_params)
                    .annotate(month=TruncMonth('purchase_date')).values('month', 'purchase_price', 'quantity')
                    .annotate(
            total_amount=Sum(F('purchase_price') * F('quantity'))).order_by('month')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            results[date_str] = item['total_amount']
        return results

    def get_portfolio_allocation(self):
        holdings = Holding.objects.select_related('company').filter(portfolio_id=1)

        sector_allocation = defaultdict(Decimal)
        industry_allocation = defaultdict(Decimal)

        sector_data = holdings.values('company__sector__name').annotate(
            total_value=Sum('total_investment')
        )
        industry_data = holdings.values('company__industry__name').annotate(
            total_value=Sum('total_investment')
        )

        for sector in sector_data:
            sector_name = sector['company__sector__name']
            sector_allocation[sector_name] = Decimal(sector['total_value'] or 0)

        for industry in industry_data:
            industry_name = industry['company__industry__name']
            industry_allocation[industry_name] = Decimal(industry['total_value'] or 0)

        return {
            "sector_allocation": sector_allocation,
            "industry_allocation": industry_allocation,
        }

    def get_performance(self):
        holdings = Holding.objects.select_related('company').filter(portfolio_id=1)
        aggregated_data = holdings.aggregate(
            total_investment=Sum('total_investment'),
            current_portfolio_value=Sum('current_value'),
            total_profit=Sum('profit_loss')
        )
        total_investment = aggregated_data['total_investment'] or 0
        current_portfolio_value = aggregated_data['current_portfolio_value'] or 0
        total_profit = aggregated_data['total_profit'] or 0

        return {
            "total_investment": total_investment,
            "current_portfolio_value": current_portfolio_value,
            "total_profit": total_profit
        }

