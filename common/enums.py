from enum import Enum


class AccountTypes(Enum):
    RAKUTEN_CARD = 1
    EPOS_CARD = 2
    DOCOMO_CARD = 3
    MIZUHO = 4
    TOKYU_CARD = 5


class AccountProviders(Enum):
    RAKUTEN = 'Rakuten'
    EPOS = 'EPOS'
    DOCOMO = 'Docomo'
    MIZUHO = 'Mizuho'
    TOKYU = 'Tokyu'


class DataSource(Enum):
    IMPORT = 1
    MANUAL_ENTRY = 2


class WorkflowContextType(Enum):
    TRANSACTION_FILES = 'TRANSACTION'
