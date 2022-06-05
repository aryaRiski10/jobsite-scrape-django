from django.db import models
# Create your models here.

class Jobs(models.Model):
    job_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    requirement = models.TextField()
    posted = models.TextField()
    date_posted = models.DateField()
    image = models.TextField()
    link = models.TextField()

    class Meta:
        managed = False
        db_table = 'jobs'
        