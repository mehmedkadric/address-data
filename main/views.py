# views.py
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView, View
from .forms import QueryForm
from .models import Query, AddressParsed
from .utils.address_utils import parse_address_components, process_nominatim

logger = logging.getLogger(__name__)


class AddressEntryView(View):
    """Handles address entry (create, list, delete)."""

    def get(self, request):
        form = QueryForm()
        queries = Query.objects.all().order_by('-timestamp')
        parsed_addresses = AddressParsed.objects.select_related('query').all()

        # Prepare data for map visualization
        parsed_addresses_arr = []
        for pa in parsed_addresses:
            coords = pa.query.nominatim_coordinates
            if coords:
                lon, lat = [c.strip() for c in coords.split(',')]
                parsed_addresses_arr.append({
                    'lat': lat,
                    'lon': lon,
                    'displayName': pa.query.nominatim_display_name,
                    'query': pa.query.address,
                })

        context = {
            'form': form,
            'queries': queries,
            'parsed_addresses': parsed_addresses,
            'parsed_addresses_arr': json.dumps(parsed_addresses_arr),
        }
        return render(request, 'address_entry.html', context)

    def post(self, request):
        form = QueryForm(request.POST)
        if form.is_valid():
            messages.info(request, "Saving...")
            query = form.save()

            # Geocode
            messages.info(request, "Geocoding...")
            geocoded_info = process_nominatim(query.address)
            query.nominatim_display_name = geocoded_info['nominatim_display_name']
            query.nominatim_coordinates = geocoded_info['nominatim_coordinates']
            query.save()
            messages.success(request, "Geocoded.")

            # Parse and save address
            self.parse_and_save_address(query, query.address)
            messages.success(request, "New entry added.")
            return redirect('address_entry')
        else:
            messages.error(request, "Invalid form submission.")
            return redirect('address_entry')

    def parse_and_save_address(self, query, raw_address):
        parsed_components = parse_address_components(raw_address)
        AddressParsed.objects.create(
            query=query,
            house=parsed_components.get('house'),
            category=parsed_components.get('category'),
            near=parsed_components.get('near'),
            house_number=parsed_components.get('house_number'),
            road=parsed_components.get('road'),
            unit=parsed_components.get('unit'),
            level=parsed_components.get('level'),
            staircase=parsed_components.get('staircase'),
            entrance=parsed_components.get('entrance'),
            po_box=parsed_components.get('po_box'),
            postcode=parsed_components.get('postcode'),
            suburb=parsed_components.get('suburb'),
            city_district=parsed_components.get('city_district'),
            city=parsed_components.get('city'),
            island=parsed_components.get('island'),
            state_district=parsed_components.get('state_district'),
            state=parsed_components.get('state'),
            country_region=parsed_components.get('country_region'),
            country=parsed_components.get('country'),
            world_region=parsed_components.get('world_region'),
        )


class DeleteQueryView(View):
    """Delete a Query entry."""

    def get(self, request, pk):
        try:
            query = get_object_or_404(Query, pk=pk)
            query.delete()
            messages.warning(request, "Entry removed.")
        except Exception as e:
            logger.error(f"Error deleting query: {e}")
            messages.error(request, f"{e}")
        return redirect('address_entry')


class AnalysisView(TemplateView):
    template_name = 'analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve user inputs or defaults
        reference_address = self.request.GET.get('reference_address', 'hitna pomoc sarajevo')
        distance_threshold = float(self.request.GET.get('distance_threshold', 2.0))

        # Geocode reference address
        ref_geocode = process_nominatim(reference_address)
        ref_coordinates = ref_geocode['nominatim_coordinates']
        if ref_coordinates:
            ref_lon, ref_lat = [float(c.strip()) for c in ref_coordinates.split(',')]
        else:
            # Fallback to Sarajevo center if geocoding fails
            ref_lat, ref_lon = 43.8563, 18.4131

        parsed_addresses = AddressParsed.objects.select_related('query')

        # Frequency distributions for multiple fields
        fields_to_analyze = ['city', 'road', 'country', 'state', 'postcode', 'suburb', 'city_district']
        field_frequency = {}
        for field in fields_to_analyze:
            freq_dict = {}
            total_count = 0
            unknown_count = 0
            for pa in parsed_addresses:
                val = getattr(pa, field, None) or 'Unknown'
                total_count += 1
                if val == 'Unknown':
                    unknown_count += 1
                freq_dict[val] = freq_dict.get(val, 0) + 1

            # Remove 'Unknown' from the displayed distribution
            if 'Unknown' in freq_dict:
                del freq_dict['Unknown']
            field_frequency[field] = {
                'freq': freq_dict,
                'total': total_count,
                'unknown_count': unknown_count
            }

        # Default charts for city and road frequency
        city_info = field_frequency['city']
        road_info = field_frequency['road']

        city_labels = list(city_info['freq'].keys())
        city_data = list(city_info['freq'].values())
        city_unknown_count = city_info['unknown_count']
        city_total = city_info['total']
        city_unknown_percentage = (city_unknown_count / city_total * 100) if city_total else 0

        road_labels = list(road_info['freq'].keys())
        road_data = list(road_info['freq'].values())
        road_unknown_count = road_info['unknown_count']
        road_total = road_info['total']
        road_unknown_percentage = (road_unknown_count / road_total * 100) if road_total else 0

        # Calculate distances for all points and filter by threshold
        all_points = []
        close_points = []
        distances = []  # store all distances for distribution
        for pa in parsed_addresses:
            coords = pa.query.nominatim_coordinates
            if coords:
                lon, lat = coords.split(',')
                lat = float(lat.strip())
                lon = float(lon.strip())
                dist = self.haversine_distance(ref_lon, ref_lat, lon, lat)
                distances.append(dist)
                point_data = {
                    'lat': lat,
                    'lon': lon,
                    'displayName': pa.query.nominatim_display_name,
                    'address': pa.query.address,
                    'distance': round(dist, 3)
                }
                all_points.append(point_data)
                if dist <= distance_threshold:
                    close_points.append(point_data)

        # Distance distribution (binning)
        # Let's create bins of size 1 km for simplicity up to max distance
        if distances:
            max_dist = max(distances)
        else:
            max_dist = 0
        bin_size = 1.0
        bins = []
        bin_counts = []
        if max_dist > 0:
            num_bins = int(max_dist // bin_size) + 1
            # Initialize bins
            for i in range(num_bins):
                bins.append(f"{i * bin_size}-{(i + 1) * bin_size} km")
                bin_counts.append(0)
            # Count frequencies
            for d in distances:
                idx = int(d // bin_size)
                if idx >= num_bins:  # edge case if d == max_dist exactly
                    idx = num_bins - 1
                bin_counts[idx] += 1
        else:
            # If no distances, just have one bin
            bins = ["0-1 km"]
            bin_counts = [0]

        # Prepare field_frequency for JSON to enable dropdown switching
        # We'll send only the freq part, along with unknown counts, etc.
        field_freq_data = {}
        for f in fields_to_analyze:
            freq = field_frequency[f]['freq']
            # Convert dict to lists
            labels = list(freq.keys())
            data = list(freq.values())
            field_freq_data[f] = {
                'labels': labels,
                'data': data,
                'unknown_count': field_frequency[f]['unknown_count'],
                'total': field_frequency[f]['total']
            }

        context.update({
            'city_labels': city_labels,
            'city_data': city_data,
            'city_unknown_count': city_unknown_count,
            'city_unknown_percentage': round(city_unknown_percentage, 2),

            'road_labels': road_labels,
            'road_data': road_data,
            'road_unknown_count': road_unknown_count,
            'road_unknown_percentage': round(road_unknown_percentage, 2),

            'close_points': json.dumps(close_points),
            'all_points': json.dumps(all_points),

            'distance_bins': bins,
            'distance_bin_counts': bin_counts,

            'field_frequency': json.dumps(field_freq_data),
            'fields_available': fields_to_analyze,
            'default_field': 'country',

            'reference_address': reference_address,
            'distance_threshold': distance_threshold,
            'ref_lat': ref_lat,
            'ref_lon': ref_lon,
        })
        return context

    def haversine_distance(self, lon1, lat1, lon2, lat2):
        """Calculate haversine distance between two points in km."""
        import math
        R = 6371  # Earth radius in km
        dlon = math.radians(lon2 - lon1)
        dlat = math.radians(lat2 - lat1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(
            dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
