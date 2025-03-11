from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # USER_TYPE_CHOICES = (
    #     ('ADMIN', 'Admin'),
    #     ('CUSTOMER', 'Customer'),
    #     ('SELLER', 'Seller'),
    # )
    # user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='CUSTOMER')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username