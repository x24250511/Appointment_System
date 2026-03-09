from rest_framework import serializers
from .models import Appointment, AppointmentHistory
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class AppointmentHistorySerializer(serializers.ModelSerializer):
    performed_by = UserSerializer(read_only=True)

    class Meta:
        model = AppointmentHistory
        fields = ['id', 'action', 'performed_by',
                  'notes', 'timestamp', 'changes']


class AppointmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    history = AppointmentHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'user', 'industry', 'title', 'description',
                  'appointment_date', 'appointment_time', 'location',
                  'status', 'email_sent', 'pdf_generated',
                  'created_at', 'updated_at', 'history']


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['industry', 'title', 'description', 'appointment_date',
                  'appointment_time', 'location']


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['industry', 'title', 'description', 'appointment_date',
                  'appointment_time', 'location', 'status']
