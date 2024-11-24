# https://www.am.mufg.jp/assets/pdf/tool/webapi/fund_api.pdf
# https://developer.am.mufg.jp/fund_information_all_latest/


import requests

# Fetch data from the URL
url = "https://developer.am.mufg.jp/fund_information_all_latest/"
response = requests.get(url)
print(response)
# Check if the request was successful
if response.status_code == 200:
    data = response.json()

    # Create a dictionary with fund_name and fund_cd
    fund_dict = {
        item['fund_cd']: item['fund_name']
        for item in data['datasets']
        if 'fund_cd' in item and 'fund_name' in item
    }

    print(fund_dict)
else:
    print(f"Failed to retrieve data: {response.status_code}")
