from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from authApp.models import *
# Base User Profile Model (Abstract)
class BaseProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    class Meta:
        abstract = True

# Patient Model
class Patient(BaseProfile):
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    medical_history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"

# Doctor Model
class Doctor(BaseProfile):
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.IntegerField(validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.specialization})"

# Doctor Model
class LabTech(BaseProfile):
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.IntegerField(validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.specialization})"

# Laboratory Model
class Laboratory(BaseProfile):
    lab_tech = models.ForeignKey(LabTech, on_delete=models.CASCADE, null=True, blank=True)
    lab_name = models.CharField(max_length=100)
    accreditation_number = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=100, default='voicepowered@lab.com')
    location = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, default="Ready to Serve you at best standards")
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lab: {self.lab_name}"

# Symptom Model
class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    swahili_name = models.CharField(default="swahili", max_length=50)
    def __str__(self):
        return self.name

# Disease Model
class Disease(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    related_symptoms = models.ManyToManyField(Symptom, related_name='related_diseases')
    doctors = models.ManyToManyField(Doctor, related_name="doctors")
    def __str__(self):
        return self.name

# Consultation Model
class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='consultations', null=True, blank=True)
    symptoms = models.ManyToManyField(Symptom, related_name='consultations')
    disease = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation: {self.patient.user.get_full_name()} - {self.disease}"

# Medical Test Model
class MedicalTest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Prescribed Test Model
class PrescribedTest(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='prescribed_tests')
    test = models.ManyToManyField(MedicalTest, related_name="medicat_tests")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        test_names = ", ".join(test.name for test in self.test.all())
        patient_name = self.consultation.patient.user.get_full_name() if self.consultation and self.consultation.patient else "Unknown"
        return f"Prescribed Test: {test_names} for {patient_name}"

# Test Result Model



class TestResult(models.Model):
    prescribed_test = models.OneToOneField(PrescribedTest, on_delete=models.CASCADE, related_name='test_result')
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE, related_name='test_results')
    result_file = models.FileField(upload_to='test_results/')
    notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test Result: {self.prescribed_test.test.name} for {self.prescribed_test.consultation.patient.user.get_full_name()}"

# Prescription Model
class Prescription(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='prescription')
    medication = models.TextField()
    dosage = models.TextField()
    instructions = models.TextField(blank=True, null=True)
    prescribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.consultation.patient.user.get_full_name()}"




from django.db import models
from django.utils import timezone

class TestOrder(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=20, unique=True)
    test_type = models.ForeignKey(MedicalTest, on_delete=models.CASCADE, related_name='orders')
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='test_orders')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    received_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order #{self.order_id} - {self.test_type.name} for {self.patient.user.get_full_name()}"
