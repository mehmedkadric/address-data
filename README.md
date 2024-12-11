# Address Data Analysis

This Django project demonstrates how to:
- Parse address data into structured components using `libpostal`.
- Geocode addresses using `Nominatim` (OpenStreetMap).
- Visualize data on a `Leaflet` map.
- Present frequency distributions and other insights via `Chart.js`.

## Features
- Data Entry: Add, store, parse, and geocode addresses.
- Analysis Dashboard: Frequency charts, distance distribution, and customizable reference point with radius.

## Quick Start
1. Clone the repository
2. Install dependecies: `pip install -r requirements.txt`
3. Apply migrations: `python manage.py migrate`
4. Run the server: `python manage.py runserver`

Open `http://127.0.0.1:8000` in your browser.