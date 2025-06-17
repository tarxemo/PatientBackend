# management/commands/create_doctors_for_diseases.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from authApp.models import CustomUser
from patient.models import Doctor, Disease
import random

class Command(BaseCommand):
    help = 'Creates three doctors for each disease in the system'

    def handle(self, *args, **options):
        # Common doctor names list
        doctor_names = [
            ("James", "Smith"),
            ("Michael", "Johnson"),
            ("Robert", "Williams"),
            ("David", "Brown"),
            ("Richard", "Jones"),
            ("Charles", "Miller"),
            ("Joseph", "Davis"),
            ("Thomas", "Garcia"),
            ("Daniel", "Rodriguez"),
            ("Matthew", "Wilson"),
            ("Anthony", "Martinez"),
            ("Donald", "Anderson"),
            ("Mark", "Taylor"),
            ("Paul", "Thomas"),
            ("Steven", "Hernandez"),
            ("Andrew", "Moore"),
            ("Kenneth", "Martin"),
            ("Joshua", "Jackson"),
            ("Kevin", "Thompson"),
            ("Brian", "White")
        ]

        # Get all diseases (assuming there are only 3)
        diseases = Disease.objects.all()
        if diseases.count() != 3:
            self.stdout.write(self.style.ERROR('There should be exactly 3 diseases in the system'))
            return

        doctors_created = 0

        for disease in diseases:
            # Create 3 doctors for each disease
            for i in range(3):
                if not doctor_names:
                    self.stdout.write(self.style.WARNING('Ran out of doctor names!'))
                    break

                # Get a random name from the list
                first_name, last_name = random.choice(doctor_names)
                doctor_names.remove((first_name, last_name))  # Remove to avoid duplicates
                
                # Create username (firstname.lastname)
                username = f"{first_name.lower()}.{last_name.lower()}"
                email = f"{username}@medic.com"

                # Create the user
                user = CustomUser.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=make_password('doctor123'),  # Default password
                    user_type='doctor',
                    is_verified=True
                )

                # Create the doctor profile
                doctor = Doctor.objects.create(
                    user=user,
                    specialization=disease.name,  # Using disease name as specialization
                    license_number=f"MD-{random.randint(100000, 999999)}",
                    years_of_experience=random.randint(5, 30),
                    is_available=True
                )

                # Add doctor to disease
                disease.doctors.add(doctor)
                disease.save()

                doctors_created += 1
                self.stdout.write(self.style.SUCCESS(f'Created Dr. {first_name} {last_name} for {disease.name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {doctors_created} doctors for {diseases.count()} diseases'))