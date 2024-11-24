from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

from investments.models import StockPurchaseHistory, Holding


class DashboardService:

    def get_monthly_invested_amount(self, year):
        filter_params = {}
        if year:
            filter_params['purchase_date__year'] = year
        queryset = (StockPurchaseHistory.objects.select_related('company')
                    .filter(**filter_params)
                    .annotate(month=TruncMonth('date')).values('month', 'purchase_price', 'quantity')
                    .annotate(
                        total_amount=Sum(F('purchase_price') * F('quantity'))).order_by('month')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            results[date_str] = item['total_amount']
        return results

    def get_portfolio_allocation(self):
        holdings = Holding.objects.select_related('company')

        # Dictionaries to store allocations
        sector_allocation = defaultdict(Decimal)
        industry_allocation = defaultdict(Decimal)
        total_allocation = Decimal(0)

        # Calculate total value and allocations by sector and industry
        for holding in holdings:
            if holding.company and holding.current_value:
                sector_name = holding.company.sector.name
                industry_name = holding.company.industry.name
                holding_value = holding.current_value

                sector_allocation[sector_name] += holding_value
                industry_allocation[industry_name] += holding_value
                total_allocation += holding_value

        return {
            "sector_allocation": sector_allocation,
            "industry_allocation": industry_allocation,
            "total_allocation": total_allocation,
        }