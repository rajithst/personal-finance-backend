import numpy as np
import pandas as pd

from workflow.import_workflow import ImportWorkflowContract

def clean_numeric_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Clean and convert a column to numeric by removing commas.

    Parameters:
        df (pd.DataFrame): The input DataFrame.
        column_name (str): Column to clean.

    Returns:
        pd.DataFrame: DataFrame with the cleaned column.
    """
    df[column_name] = df[column_name].str.replace(',', '').astype(float).round(2)
    return df

class BaseLoader(object):
    """
    A base class for data loaders, providing common functionality such as
    setting default properties and validating DataFrames.
    """
    def set_default_props(self, df, account):
        """
        Add default properties to the DataFrame.

        Parameters:
            df (pd.DataFrame): The input DataFrame.
            account (Account): Account object containing account details.

        Returns:
            pd.DataFrame: Updated DataFrame with default properties.
        """
        params_dict = {
            'account_id': account.id,
            'notes': np.nan,
        }
        df = df.assign(**params_dict)
        return df

    def validate_dataframe(self, dataframe):
        """
        Validate that the input is a DataFrame. If not, return an empty DataFrame
        with default columns.

        Parameters:
            dataframe (pd.DataFrame): Input data.

        Returns:
            pd.DataFrame: Validated DataFrame.
        """
        if isinstance(dataframe, pd.DataFrame):
            return dataframe
        else:
            columns = ['purchase_date', 'company', 'settlement_currency', 'quantity', 'purchase_price',
                       'exchange_rate', 'stock_currency']
            return pd.DataFrame(columns=columns)


class RakutenBrokerForeignStockLoader(BaseLoader, ImportWorkflowContract):
    """
    Loader for processing foreign stock data from Rakuten brokers.
    """
    def __init__(self):
        """
        Initialize the loader with specific configurations.
        """
        super().__init__()
        self.cleanable_signatures = ['楽天ＳＰ', '/N']

    def get_read_config(self):
        """
        Return the file reading configuration.

        Returns:
            dict: File reading configuration.
        """
        return {
            'encoding': 'shift-jis'
        }

    def process_data(self, df, account):
        """
        Process raw stock data into a structured format.

        Parameters:
            df (pd.DataFrame): Raw data DataFrame.
            account (Account): Account object for the associated data.

        Returns:
            pd.DataFrame: Processed and structured DataFrame.
        """
        df.columns = ['Trade date', 'Delivery date', 'Ticker', 'Stock name', 'Account', 'Trade class',
                      'Buy/sell class', 'Credit class', 'Payment deadline',
                      'Settlement currency', 'Quantity [shares]', 'Unit price [US dollars]',
                      'Execution amount [US dollars]', 'Exchange rate', 'Fees [US dollars]',
                      'Tax [US dollar]', 'Delivery amount [US dollar]', 'Delivery amount [yen]']

        df = df[df['Buy/sell class'] == '買付']
        df.drop(columns=['Trade date', 'Stock name', 'Account', 'Trade class', 'Execution amount [US dollars]',
                         'Buy/sell class', 'Credit class', 'Payment deadline', 'Fees [US dollars]',
                         'Tax [US dollar]', 'Delivery amount [US dollar]', 'Delivery amount [yen]'], inplace=True)
        df.columns = ['purchase_date', 'company', 'settlement_currency', 'quantity', 'purchase_price',
                      'exchange_rate']
        df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%Y/%m/%d').dt.date
        df['exchange_rate'] = df['exchange_rate'].astype(float).round(2)
        df['stock_currency'] = '$'
        df = clean_numeric_column(df, 'purchase_price')
        df = self.set_default_props(df, account)
        return df

    def validate_dataframe(self, dataframe):
        return super().validate_dataframe(dataframe)


class RakutenBrokerDomesticStockLoader(BaseLoader, ImportWorkflowContract):
    """
    Loader for processing domestic stock data from Rakuten brokers.
    """
    def __init__(self):
        """
        Initialize the loader with specific configurations.
        """
        super().__init__()
        self.cleanable_signatures = ['楽天ＳＰ', '/N']

    def get_read_config(self):
        """
        Return the file reading configuration.

        Returns:
            dict: File reading configuration.
        """
        return {
            'encoding': 'shift-jis'
        }

    def process_data(self, df, account):
        """
        Process raw domestic stock data into a structured format.

        Parameters:
            df (pd.DataFrame): Raw data DataFrame.
            account (Account): Account object for the associated data.

        Returns:
            pd.DataFrame: Processed and structured DataFrame.
        """
        df.columns = ['Trade date', 'Delivery date', 'Ticker', 'Stock name', 'Market name', 'Account',
                      'Trade class',
                      'Buy/sell class', 'Credit class', 'Payment deadline', 'Quantity [shares]', 'Unit price [Yen]',
                      'Fees [yen]', 'Taxes etc. [yen]', 'Miscellaneous expenses [yen]', 'Tax category',
                      'Delivery amount [yen]', 'Building contract date', 'unit price [yen]', 'building fee [yen]',
                      'building fee consumption tax [yen]', 'interest (payment) [yen]',
                      'Interest rate (receiving) [yen]',
                      'Reverse day rate/special short selling fee (payment) [yen]',
                      'Reverse day rate (receiving) [yen]', 'Stock lending fee',
                      'Administrative expenses [yen] 〕(Tax excluded)',
                      'Name transfer fee [yen] (excluding tax)']
        df = df[df['Buy/sell class'] == '買付']
        df.drop(columns=['Trade date', 'Stock name', 'Market name', 'Account', 'Trade class', 'Buy/sell class',
                         'Credit class', 'Payment deadline', 'Fees [yen]', 'Taxes etc. [yen]', 'Fees [yen]',
                         'Taxes etc. [yen]', 'Miscellaneous expenses [yen]', 'Tax category',
                         'Building contract date', 'unit price [yen]', 'building fee [yen]',
                         'building fee consumption tax [yen]', 'interest (payment) [yen]', 'Delivery amount [yen]',
                         'Interest rate (receiving) [yen]',
                         'Reverse day rate/special short selling fee (payment) [yen]',
                         'Reverse day rate (receiving) [yen]', 'Stock lending fee',
                         'Administrative expenses [yen] 〕(Tax excluded)',
                         'Name transfer fee [yen] (excluding tax)'], inplace=True)
        df.columns = ['purchase_date', 'company', 'quantity', 'purchase_price']
        df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%Y/%m/%d').dt.date
        df['company'] = df['company'].apply(lambda x: str(x) + '.T')
        df['stock_currency'] = '¥'
        df['settlement_currency'] = '円'
        df = clean_numeric_column(df, 'purchase_price')
        df = self.set_default_props(df, account)
        return df

    def validate_dataframe(self, dataframe):
        return super().validate_dataframe(dataframe)
