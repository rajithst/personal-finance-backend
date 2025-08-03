import logging
from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

from investments.dividend.models import DividendPayment
from investments.portfolio.models import PortfolioDailyGrowth
from investments.portfolio.serializers import PortfolioDailyGrowthSerializer
from investments.stock.models import StockPurchaseHistory, Holding


class DashboardService:

    def __init__(self, portfolio_id=None, year=None):
        self.portfolio = portfolio_id
        self.year = year

    def get_monthly_invested_amount(self):
        queryset = (StockPurchaseHistory.objects.select_related('company')
                    .filter(portfolio_id=self.portfolio)
                    .annotate(year=F('purchase_date__year'), month=TruncMonth('purchase_date'))
                    .values('year', 'month')
                    .annotate(total_amount=Sum(F('purchase_price') * F('quantity')))
                    .order_by('year', 'month')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            results[date_str] = item['total_amount']
        return results

    def get_portfolio_allocation(self):
        holdings = Holding.objects.select_related('company').filter(portfolio_id=self.portfolio)

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

        sector_allocation = dict(sorted(sector_allocation.items(), key=lambda item: item[1], reverse=True))
        industry_allocation = dict(sorted(industry_allocation.items(), key=lambda item: item[1], reverse=True))
        return {
            "sector_allocation": sector_allocation,
            "industry_allocation": industry_allocation,
        }

    def get_performance(self):
        holdings = Holding.objects.select_related('company').filter(portfolio_id=self.portfolio)
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

    def get_sector_wise_performance(self):

        sector_wise_data = (
            Holding.objects
            .filter(portfolio_id=self.portfolio)
            .values('company__sector__name')
            .annotate(
                total_investment=Sum('total_investment'),
                total_current_value=Sum('current_value'),
                total_profit_loss=Sum('profit_loss')
            )
            .order_by('-total_investment')
        )

        result = []
        for sector_data in sector_wise_data:
            sector = sector_data['company__sector__name']
            result.append({
                'sector': sector,
                'total_investment': sector_data['total_investment'],
                'total_current_value': sector_data['total_current_value'],
                'total_profit_loss': sector_data['total_profit_loss']
            })
        return result

    def get_portfolio_growth_daily(self):

        growth_data = PortfolioDailyGrowth.cron_objects.filter(portfolio_id=self.portfolio).all()
        return PortfolioDailyGrowthSerializer(growth_data, many=True).data

    def get_passive_income(self):
        try:
            return DividendPayment.objects.filter(portfolio_id=self.portfolio).aggregate(
                total_amount=Sum(F('quantity') * F('amount'))
            ).get('total_amount', 0)
        except Exception as e:
            logging.exception('Failed to fetch passive income', exc_info=e)
