from io import StringIO
from django.test import TestCase, Client
from .models import Measurement
from .views import Index
from django.utils import timezone
from django.core.management import call_command
import requests


class ModelTests(TestCase):
    def setUp(self):
        self.reporting_area = "Test Area"
        self.state_code = "CA"
        self.latitude = 31.2345
        self.longitude = -123.5678
        self.aqi_value = 18
        self.aqi_category = "Good"
        self.update_timestamp = timezone.localtime()

        Measurement.objects.create(
            reporting_area=self.reporting_area,
            state_code=self.state_code,
            latitude=self.latitude,
            longitude=self.longitude,
            aqi_value=self.aqi_value,
            aqi_category=self.aqi_category,
            update_timestamp=self.update_timestamp
        )
    
    def test_measurement_created_successfully(self):
        measurement = Measurement.objects.get(reporting_area=self.reporting_area)
        self.assertEqual(measurement.state_code, self.state_code)
        self.assertEqual(measurement.latitude, self.latitude)
        self.assertEqual(measurement.longitude, self.longitude)
        self.assertEqual(measurement.aqi_value, self.aqi_value)
        self.assertEqual(measurement.aqi_category, self.aqi_category)
        self.assertEqual(measurement.update_timestamp, self.update_timestamp)

    def test_measurement_deleted_successfully(self):
        measurement = Measurement.objects.get(reporting_area=self.reporting_area)
        measurement.delete()
        all_measurements = Measurement.objects.all()
        count = all_measurements.count()
        self.assertEqual(count, 0)

class LoadDataTests(TestCase):
    def setUp(self):
        self.out = StringIO()
        call_command('load_data', stdout=self.out)
        output_lines = self.out.getvalue().split('\n')
        self.created_count = output_lines[0].split(':')[1]

    def test_api_still_valid(self):
        now = timezone.localtime()
        url = now.strftime('https://files.airnowtech.org/airnow/%Y/%Y%m%d/reportingarea.dat')
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)

    def test_load_data_output(self):
        self.assertIn('Created:', self.out.getvalue())
        self.assertIn('Deleted:', self.out.getvalue())
        self.assertIn('URL:', self.out.getvalue())
        
    def test_correct_number_of_measurements_created(self):
        all_measurements = Measurement.objects.all()
        count = all_measurements.count()
        self.assertEqual(count, int(self.created_count))

class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
       # call load_data command to make sure we have some measurements
        call_command('load_data')

    def test_lat_long_range_calculator(self):
        latitude = 40.7127753
        longitude = -74.0059728
        distance = 35
        correct_ranges = {
            'lat_min': 40.20637320834397,
            'lat_max': 41.219177391656025,
            'long_min': -74.67405920527271,
            'long_max': -73.33788639472728
        }
        view = Index()
        test_ranges = view.calculate_ranges(latitude, longitude, distance)
        self.assertEqual(correct_ranges['lat_min'], test_ranges['lat_min'])
        self.assertEqual(correct_ranges['lat_max'], test_ranges['lat_max'])
        self.assertEqual(correct_ranges['long_min'], test_ranges['long_min'])
        self.assertEqual(correct_ranges['long_max'], test_ranges['long_max'])

    def test_san_francisco_data_exists(self):
        # lat/long ranges within 100 miles of San Francisco
        ranges = {
            'lat_min': 36.32806638098277,
            'lat_max': 39.22179261901723,
            'long_min': -124.24990739565102,
            'long_max': -120.58892360434898
        }
        measurements = Measurement.objects.filter(
                latitude__gte=ranges['lat_min'],
                latitude__lte=ranges['lat_max'],
                longitude__gte=ranges['long_min'],
                longitude__lte=ranges['long_max']
            ).order_by('aqi_value')[:10]

        self.assertGreater(measurements.count(), 0)

    def test_range_limits(self):
        # lat/long ranges within 100 miles of San Francisco
        ranges = {
            'lat_min': 36.32806638098277,
            'lat_max': 39.22179261901723,
            'long_min': -124.24990739565102,
            'long_max': -120.58892360434898
        }
        measurements = Measurement.objects.filter(
                latitude__gte=ranges['lat_min'],
                latitude__lte=ranges['lat_max'],
                longitude__gte=ranges['long_min'],
                longitude__lte=ranges['long_max']
            ).order_by('aqi_value')[:10]

        for m in measurements:
            self.assertGreaterEqual(m.latitude, ranges['lat_min'])
            self.assertLessEqual(m.latitude, ranges['lat_max'])
            self.assertGreaterEqual(m.longitude, ranges['long_min'])
            self.assertLessEqual(m.longitude, ranges['long_max'])

class ClientTests(TestCase):
    @classmethod
    def setUpTestData(cls):
       # call load_data command to make sure we have some measurements
        call_command('load_data')

    def test_index_url_finds_page(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_request_without_params_gets_index_template(self):
        c = Client()
        response = c.get('/')
        for t in response.templates:
            self.assertTrue(t.name == 'index.html' or t.name == 'base.html')

    def test_request_without_distance_gets_index_template(self):
        c = Client()
        response = c.get('/?lat=36.9752283&long=-121.953293&place=Capitola')
        for t in response.templates:
            self.assertTrue(t.name == 'index.html' or t.name == 'base.html')

    def test_request_without_place_gets_index_template(self):
        c = Client()
        response = c.get('/?lat=36.9752283&long=-121.953293&dist=35')
        for t in response.templates:
            self.assertTrue(t.name == 'index.html' or t.name == 'base.html')

    def test_request_without_longitude_gets_index_template(self):
        c = Client()
        response = c.get('/?lat=36.9752283&place=Capitola&dist=35')
        for t in response.templates:
            self.assertTrue(t.name == 'index.html' or t.name == 'base.html')

    def test_request_without_latitude_gets_index_template(self):
        c = Client()
        response = c.get('/?long=-121.953293&place=Capitola&dist=35')
        for t in response.templates:
            self.assertTrue(t.name == 'index.html' or t.name == 'base.html')

    def test_request_with_all_params_gets_results_template(self):
        c = Client()
        response = c.get('/?lat=36.9752283&long=-121.953293&place=Capitola&dist=35')
        for t in response.templates:
            self.assertTrue(t.name == 'results.html' or t.name == 'base.html')
