from django.shortcuts import render
from django.views import View
from .models import Measurement
import math


class Index(View):
    def get(self, request):
        latitude = request.GET.get('lat')
        longitude = request.GET.get('long')
        distance = request.GET.get('dist')
        place = request.GET.get('place')

        if latitude and longitude and distance and place:
            # convert values to floats/ints
            latitude = float(latitude)
            longitude = float(longitude)
            distance = int(distance)

            ranges = self.calculate_ranges(latitude, longitude, distance)
            measurements = self.get_measurements_with_ranges(ranges)

            context = {'latitude': latitude, 'longitude': longitude, 'measurements': measurements, 'distance': distance, 'place': place}
            
            return render(request, 'results.html', context)

        # if get parameters are not set, we should return basic index.html
        # because user hasn't put in their location yet.
        return render(request, 'index.html')
    
    def get_measurements_with_ranges(self, ranges):
        measurements = Measurement.objects.filter(
                latitude__gte=ranges['lat_min'],
                latitude__lte=ranges['lat_max'],
                longitude__gte=ranges['long_min'],
                longitude__lte=ranges['long_max']
            ).order_by('aqi_value')[:10]

        return measurements

    def calculate_ranges(self, latitude, longitude, distance):
        # set some constants to do the distance calculation
        EARTH_RADIUS = 3960.0
        DEG_TO_RAD = math.pi/180.0
        RAD_TO_DEG = 180.0/math.pi

        lat_delta = (distance/EARTH_RADIUS)*RAD_TO_DEG

        radius_at_lat = EARTH_RADIUS*math.cos(latitude*DEG_TO_RAD)
        long_delta = (distance/radius_at_lat)*RAD_TO_DEG

        return {
            'lat_min': latitude - lat_delta,
            'lat_max': latitude + lat_delta,
            'long_min': longitude - long_delta,
            'long_max': longitude + long_delta
        }
