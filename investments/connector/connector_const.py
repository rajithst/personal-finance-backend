COMPANY_DATA_FIELDS = [

]

COMPANY_DATA_REMAP_FIELDS = {
            'exchangeShortName': 'exchange',
            'companyName': 'company_name'
}

DAILY_SNAPSHOT_FIELDS = ['symbol', 'timestamp', 'changesPercentage',
                         'change', 'price', 'dayHigh', 'dayLow',  'yearHigh', 'yearLow'
]
DAILY_SNAPSHOT_REMAP_FIELDS = {
    'timestamp': 'date',
    'changesPercentage': 'change_percentage',
    'price': 'current_price',
    'dayHigh': 'day_high_price',
    'dayLow': 'day_low_price',
    'yearHigh': 'year_high_price',
    'yearLow': 'year_low_price',
}

