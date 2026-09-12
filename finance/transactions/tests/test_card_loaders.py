import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

from common.enums import AccountProviders, DataSource
from finance.transactions.services.card_loaders import (
    BaseLoader,
    DocomoCardLoader,
    EposCardLoader,
    MizuhoBankLoader,
    RakutenCardLoader,
    TransactionProcessFactory,
)


@pytest.fixture
def mock_account():
    account = MagicMock()
    account.id = 42
    return account


class TestCardLoaders:
    def test_rakuten_card_loader(self, mock_account):
        loader = RakutenCardLoader()
        assert loader.get_read_config() == {}
        assert loader.get_expected_columns() == ['利用日', '利用店名・商品名', '利用金額']

        data = {
            '利用日': ['2026/01/15', '2026/01/16'],
            '利用店名・商品名': ['楽天ＳＰ ＳＵＰＥＲ ＭＡＲＫＥＴ', 'AMAZON.CO.JP /N'],
            '利用金額': ['1500', '3200'],
        }
        df = pd.DataFrame(data)
        processed = loader.process_data(df, mock_account)
        validated = loader.validate_dataframe(processed)

        assert len(validated) == 2
        assert validated['account_id'].iloc[0] == 42
        assert validated['source'].iloc[0] == DataSource.IMPORT.value
        assert bool(validated['is_expense'].iloc[0]) is True
        assert bool(validated['is_income'].iloc[0]) is False
        assert validated['date'].iloc[0] == datetime.date(2026, 1, 15)
        assert validated['destination'].iloc[0] == 'ＳＵＰＥＲ ＭＡＲＫＥＴ'
        assert validated['destination'].iloc[1] == 'AMAZON.CO.JP'

    def test_epos_card_loader(self, mock_account):
        loader = EposCardLoader()
        read_config = loader.get_read_config()
        assert read_config.get('encoding') == 'cp932'
        assert 'ご利用年月日' in loader.get_expected_columns()

        # Epos drops first column (.iloc[:, 1:])
        data = {
            'ダミー列': ['x', 'y'],
            'ご利用年月日': ['2026年02月10日', '2026年02月11日'],
            'ご利用場所': ['／ＮコンビニＡ', 'レストランＢ'],
            'ご利用金額（キャッシングでは元金になります）': ['500', '2500'],
        }
        df = pd.DataFrame(data)
        processed = loader.process_data(df, mock_account)
        validated = loader.validate_dataframe(processed)

        assert len(validated) == 2
        assert validated['date'].iloc[0] == datetime.date(2026, 2, 10)
        assert validated['destination'].iloc[0] == 'コンビニＡ'
        assert validated['destination'].iloc[1] == 'レストランＢ'

    def test_docomo_card_loader(self, mock_account):
        loader = DocomoCardLoader()
        assert loader.get_expected_columns() == []
        assert loader.get_read_config().get('skiprows') == 1

        data = {
            0: ['2026/03/01', '2026/03/02'],
            1: ['カフェＣ／ｉＤ', '書店Ｄ'],
            2: ['680', '1200'],
            3: ['extra_col', 'extra_col_2'],
        }
        df = pd.DataFrame(data)
        processed = loader.process_data(df, mock_account)
        validated = loader.validate_dataframe(processed)

        assert len(validated) == 2
        assert validated['date'].iloc[0] == datetime.date(2026, 3, 1)
        assert validated['destination'].iloc[0] == 'カフェＣ'
        assert validated['destination'].iloc[1] == '書店Ｄ'

    def test_mizuho_bank_loader(self, mock_account):
        loader = MizuhoBankLoader()
        assert loader.get_read_config().get('encoding') == 'shift-jis'

        data = {
            '日付': ['2026.04.01', '2026.04.02'],
            'お預入金額': ['100000', '-'],
            'お引出金額': ['-', '5000'],
            'お取引内容': ['給料', 'ATM出金'],
        }
        df = pd.DataFrame(data)
        processed = loader.process_data(df, mock_account)
        validated = loader.validate_dataframe(processed)

        # 1 income and 1 expense row
        assert len(validated) == 2
        income_rows = validated[validated['is_income'] == True]
        expense_rows = validated[validated['is_expense'] == True]
        assert len(income_rows) == 1
        assert len(expense_rows) == 1
        assert income_rows['destination'].iloc[0] == '給料'
        assert income_rows['date'].iloc[0] == datetime.date(2026, 4, 1)
        assert expense_rows['destination'].iloc[0] == 'ATM出金'
        assert expense_rows['date'].iloc[0] == datetime.date(2026, 4, 2)

    def test_clean_destinations_robustness(self):
        base = BaseLoader()
        df = pd.DataFrame({
            'destination': [' 楽天ＳＰ テスト ', None, '通常店舗'],
        })
        result = base.clean_destinations(df, ['楽天ＳＰ'])
        assert result is not None
        assert result['destination'].iloc[0] == 'テスト'
        assert result['destination_original'].iloc[0] == 'テスト'
        assert result['destination'].iloc[2] == '通常店舗'

    def test_transaction_process_factory(self):
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.RAKUTEN.value), RakutenCardLoader)
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.EPOS.value), EposCardLoader)
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.DOCOMO.value), DocomoCardLoader)
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.MIZUHO.value), MizuhoBankLoader)

        with pytest.raises(ValueError, match="Unknown source"):
            TransactionProcessFactory.get_processor("UNKNOWN_PROVIDER")
