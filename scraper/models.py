from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    PID = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=255)
    price = models.FloatField()
    url = models.URLField()
    rating = models.FloatField()
    image = models.URLField(max_length=255, blank=True, null=True)
    specifications = models.TextField()
    predicted_rating = models.FloatField(default=0.0)

class Review(models.Model):
    id=models.IntegerField(primary_key=True)
    PID = models.CharField(max_length=50)
    heading = models.CharField(max_length=255)
    review = models.TextField()
    up = models.IntegerField(default=0)
    down = models.IntegerField(default=0)

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    PID = models.CharField(max_length=50, default='',primary_key=True)
    title = models.CharField(max_length=255)
    link=models.URLField(max_length=255, default='')
    specifications = models.TextField()
    predicted_rating = models.FloatField(default=0.0)
