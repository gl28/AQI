from django.db import models

class Measurement(models.Model):
    reporting_area = models.CharField(max_length=100)
    state_code = models.CharField(max_length=2)
    latitude = models.FloatField()
    longitude = models.FloatField()
    aqi_value = models.IntegerField()
    aqi_category = models.CharField(max_length=50)
    update_timestamp = models.DateTimeField()