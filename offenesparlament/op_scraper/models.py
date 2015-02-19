from django.db import models

# Create your models here.


class Law(models.Model):
    title = models.CharField(max_length=200)
    id = models.CharField(max_length=50)
