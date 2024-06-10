COMPANY_DATA_FIELDS = ['symbol', 'companyName', 'sector', 'industry',
                       'exchangeShortName', 'currency', 'country',
                       'website', 'image', 'description'
                       ]

COMPANY_DATA_REMAP_FIELDS = {
    'exchangeShortName': 'exchange',
    'companyName': 'company_name'
}

DAILY_SNAPSHOT_FIELDS = ['symbol', 'timestamp', 'changesPercentage',
                         'change', 'price', 'dayHigh', 'dayLow', 'yearHigh', 'yearLow'
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

HISTORICAL_DATA_FIELDS = ['date', 'high', 'low', 'close', 'change', 'changePercent']
HISTORICAL_DATA_REMAP_FIELDS = {
    'changePercent': 'change_percentage',
    'close': 'current_price',
    'high': 'day_high_price',
    'low': 'day_low_price',
}