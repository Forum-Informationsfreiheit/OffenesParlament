from django.db import models

# Create your models here.


class Law(models.Model):
    title = models.CharField(max_length=200)
    # id as given by the parliament's webpage
    p_id = models.CharField(max_length=50)
