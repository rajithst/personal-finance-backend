import logging
import time

import pandas as pd
from django.conf import settings
from django.db import IntegrityError

from investments.portfolio.models import PortfolioDailyGrowth, Portfolio
from investments.stock.models import StockPurchaseHistory, Holding, StockDailyPrice
from investments.stock.service.holding_service import HoldingService

is_dev_env = settings.ENV == 'dev'
if not is_dev_env:
    try:
        from google.appengine.api import taskqueue
    except ImportError:
        logging.exception('Failed to import taskqueue from google.appengine.api')


class PortfolioGrowthDaemonService:

    def enqueue_portfolio_growth_refresh_tasks(self):
        try:
            portfolios = Portfolio.cron_objects.values_list('id', flat=True).distinct()
            if is_dev_env:
                for portfolio in portfolios:
                    service = PortfolioGrowthService(portfolio_id=portfolio)
                    service.update_portfolio_growth({})
                    time.sleep(5)
            else:
                for portfolio in portfolios:
                    taskqueue.add(
                        queue_name='sync-portfolio-growth',
                        method='GET',
                        url='/investments/portfolio/growth/refresh/',
                        target='coincraftservice',
                        headers={'Secret': f"{settings.SECRET_KEY}"},
                        params={'portfolio': portfolio}
                    )
            return True
        except Exception as e:
            logging.exception('Failed to create growth tasks: ')
            return False


class PortfolioGrowthService:
    def __init__(self, portfolio_id=None):
        self.portfolio = portfolio_id

    def update_portfolio_growth(self, request_data):
        growth = self.calculate_portfolio_growth(request_data)
        if growth.empty:
            return None

        last_growth = self.get_last_growth_from_date(request_data.get('from_date'))
        if last_growth:
            last_total_value = last_growth.portfolio_value
            growth['daily_return'].iloc[0] = (growth['portfolio_value'].iloc[0] - last_total_value) / last_total_value
        else:
            growth['daily_return'].iloc[0] = 0

        daily_growth_data = growth.to_dict('records')
        for data in daily_growth_data:
            try:
                PortfolioDailyGrowth.cron_objects.update_or_create(
                    portfolio_id=self.portfolio,
                    date=data['date'],
                    defaults={
                        'total_investment': data['total_investment'],
                        'portfolio_value': data['total_value'],
                        'daily_return': data['daily_return'],
                        'total_profit': data['total_profit'],
                    }
                )
            except IntegrityError as e:
                logging.exception(f"Error inserting or updating record: {e}")

        return daily_growth_data

    def calculate_portfolio_growth(self, request_data):

        from_date = request_data.get('from_date')
        to_date = request_data.get('to_date')
        purchase_history = self.get_purchase_history(from_date, to_date)
        if not purchase_history:
            return pd.DataFrame()
        companies = list(purchase_history.keys())
        daily_prices = self.get_price_history(companies, from_date, to_date)
        holding_growths = []
        for company in companies:
            company_purchase_history = purchase_history[company]
            company_daily_prices = daily_prices[daily_prices['company'] == company]
            holding_growth = self.get_holding_growth_daily(company_purchase_history, company_daily_prices)
            holding_growths.append(holding_growth)

        total_growth = pd.concat(holding_growths)
        daily_totals = total_growth.groupby('date').agg(
            total_investment=('total_investment', 'sum'),
            total_value=('total_value', 'sum'),
            total_profit=('profit', 'sum')
        ).reset_index()
        daily_totals['daily_return'] = daily_totals['total_value'].pct_change()
        return daily_totals

    def get_purchase_history(self, from_date=None, to_date=None):

        filter_params = {}
        if from_date:
            filter_params['purchase_date__gte'] = from_date
        if to_date:
            filter_params['purchase_date__lte'] = to_date
        purchase_histories = StockPurchaseHistory.cron_objects.filter(portfolio_id=self.portfolio, **filter_params)
        company_purchase_histories = {}
        if not purchase_histories.exists():
            companies = Holding.cron_objects.select_related('company').filter(portfolio_id=self.portfolio)
            for company in companies:
                date_range = pd.date_range(start=from_date, end=to_date)
                new_df = pd.DataFrame({'purchase_date': date_range})
                new_df['company'] = company.company.symbol
                new_df['cumulative_purchase_amount'] = company.total_investment
                new_df['cumulative_quantity'] = company.quantity
                company_purchase_histories[company.company.symbol] = new_df
        else:
            purchase_history_df = pd.DataFrame(
                purchase_histories.values('purchase_date', 'company__symbol', 'quantity', 'purchase_price'))
            purchase_history_df.columns = ['purchase_date', 'company', 'quantity', 'purchase_price']
            purchase_history_df.sort_values(by='purchase_date', ascending=True, inplace=True)
            purchase_history_df['purchase_date'] = pd.to_datetime(purchase_history_df['purchase_date'])

            companies = purchase_history_df['company'].unique().tolist()
            holding_service = HoldingService()
            stock_splits = holding_service.get_stock_splits(companies)

            for company in companies:
                company_purchase_history = purchase_history_df[purchase_history_df['company'] == company]
                stock_splits_for_company = stock_splits.get(company, [])
                adjusted_purchase_history = holding_service.apply_stock_splits(
                    company_purchase_history.to_dict('records'), stock_splits_for_company)
                company_purchase_history = pd.DataFrame(adjusted_purchase_history)
                company_purchase_history['total_purchase_amount'] = company_purchase_history['quantity'] * \
                                                                    company_purchase_history[
                                                                        'purchase_price']
                company_purchase_history['cumulative_purchase_amount'] = company_purchase_history[
                    'total_purchase_amount'].cumsum()
                company_purchase_history['cumulative_quantity'] = company_purchase_history['quantity'].cumsum()

                start_date = company_purchase_history['purchase_date'].min()
                end_date = pd.to_datetime('today')
                date_range = pd.date_range(start=start_date, end=end_date)
                new_df = pd.DataFrame({'purchase_date': date_range})
                new_df['company'] = company
                merged_df = pd.merge(new_df, company_purchase_history, on=['purchase_date', 'company'], how='left')
                merged_df = merged_df.ffill()
                new_merged = merged_df[
                    ['purchase_date', 'company', 'cumulative_purchase_amount', 'cumulative_quantity']]
                company_purchase_histories[company] = new_merged
        return company_purchase_histories

    def get_price_history(self, companies, from_date=None, to_date=None):

        filter_params = {}
        if companies:
            if isinstance(companies, list):
                filter_params['company__symbol__in'] = companies
            else:
                raise ValueError("companies should be a list of company symbols")
        else:
            raise ValueError("companies should be a list of company symbols")
        if from_date:
            filter_params['date__gte'] = from_date
        if to_date:
            filter_params['date__lte'] = to_date
        daily_prices = StockDailyPrice.cron_objects.filter(**filter_params).order_by('-date')
        daily_prices_df = pd.DataFrame(
            daily_prices.values('date', 'company__symbol', 'current_price'))
        daily_prices_df.columns = ['date', 'company', 'current_price']
        daily_prices_df.sort_values(by='date', ascending=True, inplace=True)
        daily_prices_df['date'] = pd.to_datetime(daily_prices_df['date'])
        return daily_prices_df

    def get_holding_growth_daily(self, purchase_history, daily_prices):
        purchase_history_df = purchase_history.copy()
        daily_prices_df = daily_prices.copy()
        merged_df = pd.merge(purchase_history_df, daily_prices_df, how='inner', left_on=['company', 'purchase_date'],
                             right_on=['company', 'date'])
        merged_df['current_price'] = merged_df['current_price'].astype(float)
        merged_df['cumulative_purchase_amount'] = merged_df['cumulative_purchase_amount'].astype(float)
        merged_df['cumulative_quantity'] = merged_df['cumulative_quantity'].astype(float)

        merged_df['profit'] = merged_df['current_price'] * merged_df['cumulative_quantity'] - merged_df[
            'cumulative_purchase_amount']
        merged_df['total_value'] = merged_df['current_price'] * merged_df['cumulative_quantity']
        merged_df = merged_df[['purchase_date', 'company', 'cumulative_purchase_amount', 'total_value', 'profit', ]]
        merged_df.columns = ['date', 'company', 'total_investment', 'total_value', 'profit']
        return merged_df

    def get_last_growth_from_date(self, from_date):
        if from_date:
            last_growth = PortfolioDailyGrowth.cron_objects.filter(portfolio_id=self.portfolio, date=from_date)
            if last_growth.exists():
                return last_growth.first()
        return None
