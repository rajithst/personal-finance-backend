
from datetime import date
from decimal import Decimal

from investments.connector.market_api import MarketApi
from investments.models import Holding
from investments.serializers.serializers import HoldingSerializer


class HoldingHandler(object):

    def __init__(self):
        self.market_api = MarketApi()

    def merge_holding(self, symbol, update_params):
        if not symbol or not update_params:
            raise ValueError('No symbol or update_params provided')

        quantity = update_params.get('quantity', None)
        purchase_price = update_params.get('purchase_price', None)
        if not quantity or not purchase_price:
            raise ValueError('No quantity or  purchase_price provided')
        exist_holding = Holding.objects.filter(company=symbol).first()
        if exist_holding:
            current_market_price = exist_holding.current_price
            if exist_holding.price_updated_at < date.today():
                market_prices = self.update_daily_price(symbols=[symbol])
                current_market_price = market_prices[symbol]

            new_quantity = quantity + exist_holding.quantity
            all_purchase_sum = exist_holding.total_investment + Decimal(quantity * purchase_price)
            average_price = all_purchase_sum / new_quantity
            current_value = round(current_market_price * new_quantity, 2)
            profit_loss = Decimal(current_value) - all_purchase_sum
            Holding.objects.filter(company=symbol).update(quantity=new_quantity,
                                                          average_price=average_price,
                                                          current_value=current_value,
                                                          profit_loss=profit_loss,
                                                          total_investment=all_purchase_sum)

        else:
            update_params['average_price'] = purchase_price
            update_params['total_investment'] = round(purchase_price * quantity, 2)
            serializer = HoldingSerializer(data=update_params)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
            self.update_daily_price(symbols=[symbol])

    def update_daily_price(self, symbols=None):
        if not symbols:
            holdings = Holding.objects.all()
            tickers = holdings.values_list('company', flat=True).distinct()
        else:
            if not isinstance(symbols, list):
                raise ValueError('symbols must be a list of strings')
            tickers = symbols
            holdings = Holding.objects.filter(company_id__in=tickers)
        daily_data = self.market_api.get_day_snapshot(tickers=list(tickers))
        new_market_prices = {}
        for data in daily_data:
            current_holding = holdings.filter(company=data.get('symbol')).first()
            current_price = data.get('current_price')
            current_value = current_price * current_holding.quantity
            profit_loss = Decimal(current_value) - current_holding.total_investment
            Holding.objects.filter(company_id=data['symbol']).update(current_price=current_price,
                                                                     current_value=current_value,
                                                                     profit_loss=profit_loss,
                                                                     price_updated_at=date.today())
            new_market_prices[data['symbol']] = current_price
        return new_market_prices
