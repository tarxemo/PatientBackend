from django.core.management.base import BaseCommand
from authApp.models import CustomUser
from patient.models import Patient, LabTech
from django.db import IntegrityError, transaction

class Command(BaseCommand):
    help = 'Create user profiles (Patient, LabTech) for all users, handling missing data and errors safely'

    def handle(self, *args, **options):
        users = CustomUser.objects.all()

        for user in users:
            # -------------------
            # Create Patient
            # -------------------
            if not Patient.objects.filter(user=user).exists():
                try:
                    Patient.objects.create(user=user)
                    self.stdout.write(self.style.SUCCESS(f'✅ Created Patient profile for {user.username}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to create Patient for {user.username}: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Patient profile already exists for {user.username}'))

            # -------------------
            # Create LabTech with safe defaults
            # -------------------
            if not LabTech.objects.filter(user=user).exists():
                try:
                    # Supply all required non-null fields with safe default values
                    LabTech.objects.create(
                        user=user,
                        years_of_experience=0,      # Default: 0 years
                        phone_number="N/A",         # Or a real default
                        gender="N/A",               # Replace with valid default from choices if applicable
                        address="N/A",              # Avoid blank address
                    )
                    self.stdout.write(self.style.SUCCESS(f'✅ Created LabTech profile for {user.username}'))
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f'❌ IntegrityError for LabTech ({user.username}): {str(e)}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to create LabTech for {user.username}: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ LabTech profile already exists for {user.username}'))

        self.stdout.write(self.style.SUCCESS("\n🎉 Profile creation process completed."))
