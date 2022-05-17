from django.db import models
import datetime

# Create your models here.
class Jobs(models.Model):
    job_id = models.IntegerField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    company = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    requirement = models.TextField(blank=True, null=True)
    posted = models.TextField(blank=True, null=True)
    datetime_posted = models.DateField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jobs'
   