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
        assert expense_rows['is_payment'].iloc[0] == True
        assert income_rows['is_payment'].iloc[0] == False

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

    def test_tokyu_card_loader_with_purchases(self, mock_account, monkeypatch):
        from finance.transactions.services.card_loaders import TokyuCardLoader
        loader = TokyuCardLoader()
        assert loader.get_expected_columns() == []
        assert loader.get_read_config().get('encoding') == 'cp932'

        # Raw Tokyu Card CSV data with purchase
        raw_rows = [
            ["会員名：山田　太郎", "4543-85**-****-****", "会員番号"],
            ["2025/08/07", "ユニクロ", "11960", "0", "1回払い", "", "", ""],
            ["", "ショッピングお支払金額合計", "", "", "", "", "11960", ""],
            ["", "キャッシングお支払金額合計", "", "", "", "", "53747", ""],
            ["", "", "11960", "0", "", "", "65707", ""],
        ]
        df = pd.DataFrame(raw_rows)

        # Mock Gemini extractor to return structured TokyuStatementSchema
        from finance.transactions.services.tokyu_card_service import (
            TokyuStatementSchema,
            TokyuTransactionItem,
        )
        mock_parsed = TokyuStatementSchema(
            statement_year_month="2025-08",
            payment_date="2025-08-10",
            card_last4="85**",
            total_payment_due=65707.0,
            shopping_subtotal=11960.0,
            cashing_principal=50000.0,
            cashing_interest=3747.0,
            transactions=[
                TokyuTransactionItem(
                    date="2025-08-07",
                    destination="ユニクロ",
                    amount=11960.0,
                    payment_type="1回払い",
                    is_fee_or_interest=False,
                )
            ],
        )
        monkeypatch.setattr(
            "finance.transactions.services.tokyu_card_service.extract_tokyu_statement",
            lambda *args, **kwargs: mock_parsed,
        )

        processed = loader.process_data(df, mock_account)
        validated = loader.validate_dataframe(processed)

        assert len(validated) >= 1
        assert validated['date'].iloc[0] == datetime.date(2025, 8, 7)
        assert validated['destination'].iloc[0] == 'ユニクロ'
        assert float(validated['amount'].iloc[0]) == 11960.0
        assert bool(validated['is_expense'].iloc[0]) is True
        assert bool(validated['is_payment'].iloc[0]) is False

    def test_tokyu_card_loader_installment_only_month(self, mock_account, monkeypatch):
        """Month like 202608.csv where there are no purchases, only installment/cashing."""
        from finance.transactions.services.card_loaders import TokyuCardLoader
        loader = TokyuCardLoader()

        raw_rows = [
            ["会員名：山田　太郎", "4543-85**-****-****", "会員番号"],
            ["", "キャッシングお支払金額合計", "", "", "", "", "54315", ""],
            ["", "", "0", "0", "", "", "54315", ""],
        ]
        df = pd.DataFrame(raw_rows)

        from finance.transactions.services.tokyu_card_service import (
            TokyuStatementSchema,
            TokyuTransactionItem,
        )
        mock_parsed = TokyuStatementSchema(
            statement_year_month="2026-08",
            payment_date="2026-08-10",
            card_last4="85**",
            total_payment_due=54315.0,
            shopping_subtotal=0.0,
            cashing_principal=50000.0,
            cashing_interest=4315.0,
            transactions=[
                TokyuTransactionItem(
                    date="2026-08-10",
                    destination="Tokyu Card Cashing Installment Fee",
                    amount=4315.0,
                    payment_type="キャッシング利息",
                    is_fee_or_interest=True,
                )
            ],
        )
        monkeypatch.setattr(
            "finance.transactions.services.tokyu_card_service.extract_tokyu_statement",
            lambda *args, **kwargs: mock_parsed,
        )

        processed = loader.process_data(df, mock_account)
        validated = loader.validate_dataframe(processed)

        assert len(validated) == 1
        assert validated['date'].iloc[0] == datetime.date(2026, 8, 10)
        assert 'Installment Fee' in validated['destination'].iloc[0]
        assert float(validated['amount'].iloc[0]) == 4315.0
        assert bool(validated['is_expense'].iloc[0]) is True

    def test_transaction_process_factory(self):
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.RAKUTEN.value), RakutenCardLoader)
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.EPOS.value), EposCardLoader)
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.DOCOMO.value), DocomoCardLoader)
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.MIZUHO.value), MizuhoBankLoader)
        from finance.transactions.services.card_loaders import TokyuCardLoader
        assert isinstance(TransactionProcessFactory.get_processor(AccountProviders.TOKYU.value), TokyuCardLoader)

        with pytest.raises(ValueError, match="Unknown source"):
            TransactionProcessFactory.get_processor("UNKNOWN_PROVIDER")
