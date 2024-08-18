from enum import Enum


class AccountTypes(Enum):
    RAKUTEN_CARD = 1
    EPOS_CARD = 2
    DOCOMO_CARD = 3
    CASH = 4


class CardTypes(Enum):
    RAKUTEN = 'Rakuten'
    EPOS = 'Epos'
    DOCOMO = 'Docomo'
    CASH = 'Cash'


class DataSource(Enum):
    IMPORT = 1
    MANUAL_ENTRY = 2