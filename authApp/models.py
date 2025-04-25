from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    PHONE_NUMBER_MAX_LENGTH = 15
    USER_TYPE_CHOICES = [

        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
        ('patient', 'Patient'),
        ('lab_technician', 'Lab Technician'),
    ]

    phone_number = models.CharField(max_length=PHONE_NUMBER_MAX_LENGTH, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_online = models.BooleanField(default=True)  # Track online status
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='patient',  # Default to patient, but you can adjust this
    )

    def __str__(self):
        return self.username
