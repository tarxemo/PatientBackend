import csv
import os
import random
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from authApp.models import CustomUser
from patient.models import Patient, Doctor, LabTech


class Command(BaseCommand):
    help = 'Imports healthcare data from Salaries.csv and creates random Patients, Doctors, and LabTechs'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(settings.BASE_DIR, "patient", "Salaries.csv")

        if not os.path.exists(csv_path):
            self.stderr.write("CSV file not found.")
            return

        patients_created, doctors_created, labtechs_created = 0, 0, 0
        errors = []

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            entries = list(reader)
            random.shuffle(entries)

            for i, row in enumerate(entries):
                try:
                    full_name = row.get("EmployeeName", "").strip()
                    if not full_name:
                        self.stdout.write("Skipping row with missing name.")
                        continue

                    name_parts = full_name.split()
                    if len(name_parts) < 2:
                        errors.append(f"Invalid name format: {full_name}")
                        continue

                    first_name = name_parts[0].capitalize()
                    last_name = name_parts[-1].capitalize()
                    username = f"{first_name.lower()}{last_name.lower()}"
                    email = f"{username}@gmail.com"
                    password = last_name.lower()

                    if CustomUser.objects.filter(username=username).exists():
                        errors.append(f"User {username} already exists.")
                        continue

                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )

                    phone_number = f"+2557{random.randint(10000000, 99999999)}"
                    address = row.get("Address", "Unknown Address")

                    if i % 4 == 0:
                        doctor = Doctor.objects.create(
                            user=user,
                            phone_number=phone_number,
                            address=address,
                            specialization=random.choice(["Cardiology", "Neurology", "Pediatrics", "Orthopedics"]),
                            license_number=f"D-{random.randint(10000, 99999)}",
                            years_of_experience=random.randint(1, 30),
                            is_available=random.choice([True, False])
                        )
                        doctors_created += 1

                    elif i % 5 == 0:
                        labtech = LabTech.objects.create(
                            user=user,
                            phone_number=phone_number,
                            address=address,
                            specialization=random.choice(["Microbiology", "Radiology", "Hematology"]),
                            license_number=f"L-{random.randint(10000, 99999)}",
                            years_of_experience=random.randint(1, 20),
                            is_available=random.choice([True, False])
                        )
                        labtechs_created += 1

                    else:
                        patient = Patient.objects.create(
                            user=user,
                            phone_number=phone_number,
                            address=address,
                            date_of_birth=datetime.now() - timedelta(days=random.randint(3650, 29200)),
                            gender=random.choice(["Male", "Female", "Other"]),
                            medical_history=row.get("MedicalHistory", "No history available")
                        )
                        patients_created += 1

                except Exception as e:
                    errors.append(str(e))

        self.stdout.write(self.style.SUCCESS(
            f"{patients_created} patients, {doctors_created} doctors, and {labtechs_created} lab technicians created."
        ))

        if errors:
            self.stdout.write(self.style.WARNING("Some errors occurred during import:"))
            for err in errors:
                self.stdout.write(f" - {err}")
