# Create a new file: management/commands/reset_diseases.py
from django.core.management.base import BaseCommand
from patient.models import Disease, Symptom, Doctor
import random

class Command(BaseCommand):
    help = 'Reset diseases to only UTI, Typhoid, and Malaria with their symptoms'

    def handle(self, *args, **options):
        # Delete all existing diseases and symptoms
        Disease.objects.all().delete()
        Symptom.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('Deleted all existing diseases and symptoms'))
        
        # Create symptoms for each disease
        disease_symptoms = {
            'UTI': [
                {'name': 'Painful urination', 'swahili_name': 'Mkojo wenye maumivu'},
                {'name': 'Frequent urination', 'swahili_name': 'Kukojoa mara kwa mara'},
                {'name': 'Urgency to urinate', 'swahili_name': 'Haraka ya kukojoa'},
                {'name': 'Lower abdominal pain', 'swahili_name': 'Maumivu ya tumbo chini'},
                {'name': 'Cloudy urine', 'swahili_name': 'Mkojo wenye usito'},
                {'name': 'Blood in urine', 'swahili_name': 'Damu katika mkojo'},
                {'name': 'Pelvic pain', 'swahili_name': 'Maumivu ya kiuno'},
                {'name': 'Fever', 'swahili_name': 'Homa'},
                {'name': 'Foul-smelling urine', 'swahili_name': 'Mkojo wenye harufu mbaya'},
                {'name': 'Burning sensation', 'swahili_name': 'Moto wakati wa kukojoa'},
            ],
            'Typhoid': [
                {'name': 'High fever', 'swahili_name': 'Homa kali'},
                {'name': 'Headache', 'swahili_name': 'Maumivu ya kichwa'},
                {'name': 'Weakness', 'swahili_name': 'Uchovu'},
                {'name': 'Stomach pain', 'swahili_name': 'Maumivu ya tumbo'},
                {'name': 'Loss of appetite', 'swahili_name': 'Kupoteza hamu ya kula'},
                {'name': 'Rash', 'swahili_name': 'Upele'},
                {'name': 'Constipation or diarrhea', 'swahili_name': 'Kuharisha au kuvimba tumbo'},
                {'name': 'Muscle aches', 'swahili_name': 'Maumivu ya misuli'},
                {'name': 'Sweating', 'swahili_name': 'Kutokwa na jasho'},
                {'name': 'Dry cough', 'swahili_name': 'Kikohozi kikavu'},
            ],
            'Malaria': [
                {'name': 'Fever', 'swahili_name': 'Homa'},
                {'name': 'Chills', 'swahili_name': 'Baridi kali'},
                {'name': 'Headache', 'swahili_name': 'Maumivu ya kichwa'},
                {'name': 'Nausea', 'swahili_name': 'Kichefuchefu'},
                {'name': 'Vomiting', 'swahili_name': 'Kutapika'},
                {'name': 'Muscle pain', 'swahili_name': 'Maumivu ya misuli'},
                {'name': 'Fatigue', 'swahili_name': 'Uchovu'},
                {'name': 'Sweating', 'swahili_name': 'Kutokwa na jasho'},
                {'name': 'Chest pain', 'swahili_name': 'Maumivu ya kifua'},
                {'name': 'Abdominal pain', 'swahili_name': 'Maumivu ya tumbo'},
            ]
        }

        # Create diseases and their symptoms
        for disease_name, symptoms in disease_symptoms.items():
            disease = Disease.objects.create(
                name=disease_name,
                description=f"Information about {disease_name}"
            )
            
            for symptom_data in symptoms:
                symptom, created = Symptom.objects.get_or_create(
                    name=symptom_data['name'],
                    defaults={'swahili_name': symptom_data['swahili_name']}
                )
                disease.related_symptoms.add(symptom)
            
            self.stdout.write(self.style.SUCCESS(f'Created {disease_name} with {len(symptoms)} symptoms'))

        # Assign random doctors to each disease
        all_doctors = list(Doctor.objects.all())
        if not all_doctors:
            self.stdout.write(self.style.WARNING('No doctors available to assign'))
            return

        for disease in Disease.objects.all():
            # Select 3 random doctors (or less if not enough available)
            num_doctors = min(3, len(all_doctors))
            selected_doctors = random.sample(all_doctors, num_doctors)
            disease.doctors.add(*selected_doctors)
            self.stdout.write(self.style.SUCCESS(
                f'Assigned {num_doctors} doctors to {disease.name}: ' +
                ', '.join([str(d) for d in selected_doctors])
            ))

        self.stdout.write(self.style.SUCCESS('Successfully reset diseases and symptoms'))