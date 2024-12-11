import re
import requests
from postal.parser import parse_address
import logging

logger = logging.getLogger(__name__)


def parse_address_components(raw_address):
    """Parse address components using 'postal.parser' library."""
    parsed_components = dict(parse_address(raw_address))
    # invert keys/values for convenience as done previously
    parsed_components = {v: k for k, v in parsed_components.items()}
    return parsed_components


def is_geometry_point(decoded_query):
    """Check if a query string is a geometry point (lat, lon)."""
    pattern = r'^[-+]?\d*\.\d+,\s*[-+]?\d*\.\d+$'
    if decoded_query and re.match(pattern, decoded_query):
        return True
    return False


def process_nominatim(address, bbox='18.248778,43.749099,18.473310,43.903187'):
    """
    Geocode the given address using Nominatim API restricted to Sarajevo bounding box.
    Return a dictionary with display_name and coordinates if found.
    """
    if is_geometry_point(address):
        # Convert from "lat, lon" to "lon, lat"
        address = address.strip()
        address = f"{address.split(',')[1].strip()},{address.split(',')[0].strip()}"

    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': address,
        'format': 'json',
        'addressdetails': 1,
        'limit': 1,
        'viewbox': bbox,
        'bounded': 1,
    }
    headers = {'User-Agent': 'Address-Data', 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error during geocoding request: {e}")
        return {'nominatim_display_name': None, 'nominatim_coordinates': None}

    data = response.json()

    out = {
        'nominatim_display_name': None,
        'nominatim_coordinates': None,
    }

    if data:
        address_info = data[0]
        center = f"{address_info.get('lon', 'N/A')}, {address_info.get('lat', 'N/A')}"
        out['nominatim_display_name'] = address_info.get('display_name', 'N/A')
        out['nominatim_coordinates'] = center

    return out
