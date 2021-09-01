from django.shortcuts import render
from .models import Measurement
import math

# Create your views here.
def index(request):

    latitude = request.GET.get('lat')
    longitude = request.GET.get('long')
    distance = request.GET.get('dist')
    place = request.GET.get('place')

    if latitude and longitude and distance and place:
        # convert values to floats/ints
        latitude = float(latitude)
        longitude = float(longitude)
        distance = int(distance)

        # set some constants to do the distance calculation
        earth_radius = 3960.0
        degrees_to_radians = math.pi/180.0
        radians_to_degrees = 180.0/math.pi

        lat_delta = (distance/earth_radius)*radians_to_degrees

        radius_at_lat = earth_radius*math.cos(latitude*degrees_to_radians)
        long_delta = (distance/radius_at_lat)*radians_to_degrees

        lat_range = (latitude - lat_delta, latitude + lat_delta)
        long_range = (longitude - long_delta, longitude + long_delta)
        
        # get all measurements within distance range
        measurements = Measurement.objects.filter(
            latitude__gte=lat_range[0],
            latitude__lte=lat_range[1],
            longitude__gte=long_range[0],
            longitude__lte=long_range[1]
        ).order_by('aqi_value')[:10]

        context = {'latitude': latitude, 'longitude': longitude, 'measurements': measurements, 'distance': distance, 'place': place}
        
        return render(request, 'results.html', context)

    return render(request, 'index.html')