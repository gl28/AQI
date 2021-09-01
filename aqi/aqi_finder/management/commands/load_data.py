from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
import requests
from aqi_finder.models import Measurement

class Command(BaseCommand):
    help = 'Loads data into the database'
    
    def handle(self, *args, **kwargs):
        
        # get the latest data form airnow
        now = timezone.localtime()
        url = now.strftime('https://files.airnowtech.org/airnow/%Y/%Y%m%d/reportingarea.dat')
        response = requests.get(url)
        data = response.text
        data_lines = data.split('\n')
        
        measurement_data = []
        
        created_count = 0
        index_error_count = 0

        for line in data_lines:
            line_split = line.split('|')

            # check if there's a time (index 2), indicating it's a measurement and not a forecast
            # check if there's a state code (index 8), indicating it's in the US
            # check if measurment type (index 11) is PM2.5
            try:
                if line_split[2] and line_split[8] and line_split[11] == 'PM2.5':

                    # select all the relevant data
                    measurement_data = [
                        # 0 - reporting_area
                        line_split[7],
                        # 1 - state_code
                        line_split[8],
                        # 2 - latitude
                        line_split[9],
                        # 3 - longitude
                        line_split[10],
                        # 4 - aqi_value
                        line_split[12],
                        # 5 - aqi_category
                        line_split[13]
                    ]

                    measurement, created = Measurement.objects.update_or_create(
                        latitude=measurement_data[2],
                        longitude=measurement_data[3],
                        defaults={
                            'reporting_area': measurement_data[0],
                            'state_code': measurement_data[1],
                            'aqi_value': measurement_data[4],
                            'aqi_category': measurement_data[5],
                            'update_timestamp': now,
                        },
                    )

                    # count how many measurements were created
                    if created == True:
                        created_count += 1

            # sometimes you get an out of range error for one line
            except IndexError:
                index_error_count += 1

        # find all measurements older than three hours
        three_h_ago = now - timezone.timedelta(hours=3)
        older_measurements = Measurement.objects.filter(update_timestamp__lt=three_h_ago)
        deleted_count = older_measurements.count()

        # delete the older measurements
        older_measurements.delete()
        
        # output a breakdown of what happened
        self.stdout.write(f"Created: {created_count}.\nIndex errors: {index_error_count}.\nDeleted: {deleted_count}\nURL: {url}")