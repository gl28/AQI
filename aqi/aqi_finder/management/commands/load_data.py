from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
import requests
from aqi_finder.models import Measurement

class Command(BaseCommand):
    help = 'Loads data into the database'
    
    def handle(self, *args, **kwargs):
        
        # get the latest data form airnow
        self.now = timezone.localtime()
        url = self.now.strftime('https://files.airnowtech.org/airnow/%Y/%Y%m%d/reportingarea.dat')
        response = requests.get(url)
        data = response.text
        created_count = self.process_data(data)
        deleted_count = self.remove_old_measurements()

        self.stdout.write(f"Created:{created_count}\nDeleted:{deleted_count}\nURL:{url}")


    def process_data(self, data):
        data_lines = data.split('\n')
        created_count = 0

        for line in data_lines:
            line_split = line.split('|')

            # check if there's a time (index 2), indicating it's a measurement and not a forecast
            # check if there's a state code (index 8), indicating it's in the US
            # check if measurment type (index 11) is PM2.5
            if len(line_split) >= 12 and line_split[2] and line_split[8] and line_split[11] == 'PM2.5':
                
                measurement_data = {
                    'reporting_area': line_split[7],
                    'state_code': line_split[8],
                    'latitude': line_split[9],
                    'longitude':line_split[10],
                    'aqi_value': line_split[12],
                    'aqi_category': line_split[13]
                }

                created = self.add_measurement(measurement_data)
                if created:
                    created_count += 1

        return created_count

    def add_measurement(self, measurement_data):
        measurement, created = Measurement.objects.update_or_create(
                    latitude=measurement_data['latitude'],
                    longitude=measurement_data['longitude'],
                    defaults={
                        'reporting_area': measurement_data['reporting_area'],
                        'state_code': measurement_data['state_code'],
                        'aqi_value': measurement_data['aqi_value'],
                        'aqi_category': measurement_data['aqi_category'],
                        'update_timestamp': self.now,
                    },
                )

        return created

    def remove_old_measurements(self):
        # find all measurements older than three hours and delete them
        three_h_ago = self.now - timezone.timedelta(hours=3)
        older_measurements = Measurement.objects.filter(update_timestamp__lt=three_h_ago)
        deleted_count = older_measurements.count()
        older_measurements.delete()

        return deleted_count
        