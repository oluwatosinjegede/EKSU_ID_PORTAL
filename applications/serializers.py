from rest_framework import serializers
from .models import IDApplication

class IDApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDApplication
        fields = ['passport', 'signature']
