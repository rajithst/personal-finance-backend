from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

from investments.models import StockPurchaseHistory, Holding, Portfolio, StockDailyPrice
from investments.serializers.response_serializers import ResponsePortfolioSerializer
from transactions.models import Account





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

    def get_portfolio_growth_daily(self):
        """
        Calculate the daily portfolio growth and invested amount for a given portfolio.

        :param portfolio_id: ID of the portfolio to calculate growth for
        :return: List of dictionaries containing daily growth and invested amount
        """
        # Fetch all purchase histories for the portfolio
        purchase_histories = StockPurchaseHistory.objects.filter(portfolio_id=1)

        # Fetch daily prices for the stocks in the portfolio
        stock_symbols = purchase_histories.values_list('company__symbol', flat=True).distinct()
        daily_prices = StockDailyPrice.objects.filter(company__symbol__in=stock_symbols).order_by('date')

        # Calculate daily growth and invested amount
        daily_growth = []
        daily_price_map = {}

        for price in daily_prices:
            if price.date not in daily_price_map:
                daily_price_map[price.date] = {}
            daily_price_map[price.date][price.company.symbol] = price.current_price

        current_date = daily_prices.first().date if daily_prices.exists() else None
        end_date = daily_prices.last().date if daily_prices.exists() else None

        while current_date and current_date <= end_date:
            total_invested = 0
            total_value = 0

            for purchase in purchase_histories:
                purchase_date = purchase.purchase_date
                symbol = purchase.company.symbol
                quantity = purchase.quantity

                if current_date >= purchase_date:
                    invested_amount = purchase.purchase_price * quantity
                    total_invested += invested_amount

                    if symbol in daily_price_map.get(current_date, {}):
                        current_price = daily_price_map[current_date][symbol]
                        total_value += current_price * quantity
            if total_value > 0 or total_invested > 0:
                growth = total_value - total_invested
                daily_growth.append({
                    'date': current_date,
                    'total_invested': total_invested,
                    'portfolio_value': total_value,
                    'growth': growth
                })
            current_date += timedelta(days=1)

        return daily_growth

