from rest_framework import serializers
from .models import Service , UserMessage

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'   

class UserMessageSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserMessage
        fields = '__all__'