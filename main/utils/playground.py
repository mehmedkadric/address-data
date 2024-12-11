from postal.parser import parse_address
from postal.expand import expand_address

address = "315 5th Ave #3FL, New York, NY 10016, United States"

address_parsed = parse_address(address)
address_expanded = expand_address(address)

print(address_parsed)
print(address_expanded)


import requests

def process_nominatim(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
    }

    headers = {'User-Agent': 'Address-Data', 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'}

    return requests.get(url, params=params, headers=headers).json()

print(process_nominatim("Sarajevo"))