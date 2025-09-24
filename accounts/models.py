from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=200)
    image_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    content = models.CharField(max_length=10000)
    date = models.DateTimeField()


class UserMessage(models.Model):
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(blank=True, null=True)
    message = models.TextField(max_length=1000)
    sent_at = models.DateTimeField(auto_now_add=True)



class UserMessage(models.Model):
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(blank=True, null=True)
    message = models.TextField(max_length=1000)
    sent_at = models.DateTimeField(auto_now_add=True)
