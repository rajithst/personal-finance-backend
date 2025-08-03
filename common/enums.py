from enum import Enum


class AccountTypes(Enum):
    RAKUTEN_CARD = 1
    EPOS_CARD = 2
    DOCOMO_CARD = 3
    MIZUHO = 4


class AccountProviders(Enum):
    RAKUTEN = 'Rakuten'
    EPOS = 'EPOS'
    DOCOMO = 'Docomo'
    MIZUHO = 'Mizuho'


class BrokerProviders(Enum):
    RAKUTEN = 'Rakuten'


class DataSource(Enum):
    IMPORT = 1
    MANUAL_ENTRY = 2


class WorkflowContextType(Enum):
    TRANSACTION_FILES = 'TRANSACTION'
    INVESTMENT_FILES = 'INVESTMENT'
