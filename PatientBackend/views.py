from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import login
from authApp.models import CustomUser

def doctor_wait_call(request):
    doctors = CustomUser.objects.all()
    return render(request, 'call.html', {"doctors": doctors})

def get_users(request):
    users = CustomUser.objects.exclude(username=request.user.username).values("id", "username")
    return JsonResponse(list(users), safe=False)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib import messages

User = get_user_model()

def login_view(request):
    username_param = request.GET.get('username')
    next_url = request.GET.get('next', None)

    if username_param:
        try:
            user = User.objects.get(username=username_param)
            login(request, user)
            return render(request, 'call.html', {"next_url": next_url})
        except User.DoesNotExist:
            messages.error(request, f"No user found with username: {username_param}")

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return render(request, 'call.html', {"next_url": next_url})
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

def change_user_type(reequest):
    doctors = Doctor.objects.all()
    for doctor in doctors:
        user = CustomUser.objects.get(id=doctor.user.id)
        user.user_type='doctor'
        user.save()
        print(user.user_type)

def doctor_emergence_call(request):
    # Check if there's a caller parameter in the URL
    caller_username = request.GET.get('username')
    disease = request.GET.get('disease')
    print(disease)
    print(caller_username)
    if caller_username:
        try:
            # Get the caller user
            caller = CustomUser.objects.get(username=caller_username)
            # Authenticate the user without password (not secure for production!)
            login(request, caller)  # Redirect to clean URL after auth
        except CustomUser.DoesNotExist:
            return render(request, "call.html")
    else:
            return render(request, "call.html")
    # If no caller parameter or invalid, proceed normally
    if not request.user.is_authenticated:
            return render(request, "call.html") # Redirect to normal login if not authenticated
    
    disease = Disease.objects.get(name=disease)
    doctors = disease.doctors.all()
    return render(request, "call.html", {"doctors": doctors, "disease":disease})


import csv
import os
import random
from django.conf import settings
from django.http import JsonResponse
from authApp.models import CustomUser
from patient.models import Patient, Doctor, LabTech  # Assuming these models are in 'healthApp'
from datetime import datetime, timedelta

def import_healthcare_data(request):
    """ Reads 'HealthcareData.csv' and creates random Patients, Doctors, and LabTech users. """
    csv_path = os.path.join(settings.BASE_DIR, "patient", "Salaries.csv")

    if not os.path.exists(csv_path):
        return JsonResponse({"error": "CSV file not found."})

    patients_created, doctors_created, labtechs_created = 0, 0, 0
    errors = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        entries = list(reader)
        random.shuffle(entries)  # Shuffle data to randomize assignments

        for i, row in enumerate(entries):
            try:
                full_name = row.get("EmployeeName", "").strip()
                if not full_name:
                    print("No full name")
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
                    username=username, email=email, password=password,
                    first_name=first_name, last_name=last_name
                )
                user.save()

                phone_number = f"+2557{random.randint(10000000, 99999999)}"
                address = row.get("Address", "Unknown Address")

                if i % 4 == 0:  # 25% chance of being a doctor
                    doctor = Doctor.objects.create(
                        user=user,
                        phone_number=phone_number,
                        address=address,
                        specialization=random.choice(["Cardiology", "Neurology", "Pediatrics", "Orthopedics"]),
                        license_number=f"D-{random.randint(10000, 99999)}",
                        years_of_experience=random.randint(1, 30),
                        is_available=random.choice([True, False])
                    )
                    doctor.save()
                    doctors_created += 1

                elif i % 5 == 0:  # 20% chance of being a lab technician
                    labtech = LabTech.objects.create(
                        user=user,
                        phone_number=phone_number,
                        address=address,
                        specialization=random.choice(["Microbiology", "Radiology", "Hematology"]),
                        license_number=f"L-{random.randint(10000, 99999)}",
                        years_of_experience=random.randint(1, 20),
                        is_available=random.choice([True, False])
                    )
                    labtech.save()
                    labtechs_created += 1

                else:  # 55% chance of being a patient
                    patient = Patient.objects.create(
                        user=user,
                        phone_number=phone_number,
                        address=address,
                        date_of_birth=datetime.now() - timedelta(days=random.randint(3650, 29200)),  # 10-80 years old
                        gender=random.choice(["Male", "Female", "Other"]),
                        medical_history=row.get("MedicalHistory", "No history available")
                    )
                    patient.save()
                    patients_created += 1
            
            except Exception as e:
                errors.append(str(e))

    return JsonResponse({
        "message": f"{patients_created} patients, {doctors_created} doctors, and {labtechs_created} lab technicians created successfully.",
        "errors": errors
    })


import csv
import os
import random
from django.conf import settings
from django.http import JsonResponse
from authApp.models import CustomUser
from patient.models import Patient, Doctor, LabTech, Symptom, Disease

def import_diseases_and_symptoms(request):
    """ Reads 'DiseaseSymptoms.csv' and creates Disease and Symptom entries. """
    csv_path = os.path.join(settings.BASE_DIR, "patient", "Training.csv")

    if not os.path.exists(csv_path):
        return JsonResponse({"error": "CSV file not found."})

    diseases_created = 0
    symptoms_created = 0
    errors = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        symptom_names = list(reader.fieldnames[:-1])  # All columns except the last one (prognosis)

        # Ensure all symptoms exist in the database
        for symptom_name in symptom_names:
            symptom, created = Symptom.objects.get_or_create(name=symptom_name)
            if created:
                symptoms_created += 1

        for row in reader:
            try:
                disease_name = row.get("prognosis", "").strip()
                if not disease_name:
                    continue

                disease, created = Disease.objects.get_or_create(name=disease_name)
                if created:
                    diseases_created += 1
                
                related_symptoms = []
                for symptom_name in symptom_names:
                    if row.get(symptom_name) == "1":  # If the symptom is present
                        symptom = Symptom.objects.get(name=symptom_name)
                        related_symptoms.append(symptom)
                
                disease.related_symptoms.set(related_symptoms)
                
                # Assign random five doctors to each disease
                doctors = list(Doctor.objects.order_by('?')[:5])
                disease.doctors.set(doctors)
                disease.save()
            except Exception as e:
                errors.append(str(e))

    return JsonResponse({
        "message": f"{diseases_created} diseases and {symptoms_created} symptoms created successfully.",
        "errors": errors
    })



symptom_translation = {
    "itching": "muwasho",
    "skin rash": "upele",
    "nodal skin eruptions": "milipuko ya ngozi ya nodi",
    "continuous sneezing": "kupiga chafya mara kwa mara",
    "shivering": "kutetemeka",
    "chills": "baridi kali",
    "joint pain": "maumivu ya viungo",
    "stomach pain": "maumivu ya tumbo",
    "acidity": "kiwa",
    "ulcers on tongue": "vidonda kwenye ulimi",
    "muscle wasting": "kupungua kwa misuli",
    "vomiting": "kutapika",
    "burning micturition": "hisi ya moto wakati wa kukojoa",
    "spotting urination": "madoadoa kwenye mkojo",
    "fatigue": "uchovu",
    "weight gain": "ongezeko la uzito",
    "anxiety": "wasiwasi",
    "cold hands and feets": "mikono na miguu baridi",
    "mood swings": "mabadiliko ya hisia",
    "weight loss": "kupungua uzito",
    "restlessness": "kutotulia",
    "lethargy": "uchovu mwingi",
    "patches in throat": "madoa kwenye koo",
    "irregular sugar level": "kiwango kisicho sawa cha sukari",
    "cough": "kikohozi",
    "high fever": "homa kali",
    "sunken eyes": "macho yaliyodidimia",
    "breathlessness": "kukosa hewa",
    "sweating": "kutokwa jasho",
    "dehydration": "upungufu wa maji mwilini",
    "indigestion": "kusagika vibaya kwa chakula",
    "headache": "maumivu ya kichwa",
    "yellowish skin": "ngozi ya manjano",
    "dark urine": "mkojo mweusi",
    "nausea": "kichefuchefu",
    "loss of appetite": "kukosa hamu ya kula",
    "pain behind the eyes": "maumivu nyuma ya macho",
    "back pain": "maumivu ya mgongo",
    "constipation": "kukosa choo",
    "abdominal pain": "maumivu ya tumbo",
    "diarrhoea": "kuharisha",
    "mild fever": "homa ya kawaida",
    "yellow urine": "mkojo wa njano",
    "yellowing of eyes": "manjano kwenye macho",
    "acute liver failure": "kushindwa kwa ini kwa ghafla",
    "fluid overload": "kujaa kwa maji mwilini",
    "swelling of stomach": "uvimbe wa tumbo",
    "swelled lymph nodes": "uvimbe wa tezi za limfu",
    "malaise": "hali mbaya ya afya",
    "blurred and distorted vision": "maono yaliyopungua na yaliyopotoka",
    "phlegm": "makoo",
    "throat irritation": "mwasho kwenye koo",
    "redness of eyes": "macho mekundu",
    "sinus pressure": "shinikizo la sinus",
    "runny nose": "mafua",
    "congestion": "msongamano",
    "chest pain": "maumivu ya kifua",
    "weakness in limbs": "udhaifu wa viungo",
    "fast heart rate": "mapigo ya moyo ya haraka",
    "pain during bowel movements": "maumivu wakati wa haja kubwa",
    "pain in anal region": "maumivu katika sehemu ya haja kubwa",
    "bloody stool": "kinyesi chenye damu",
    "irritation in anus": "mwasho kwenye haja kubwa",
    "neck pain": "maumivu ya shingo",
    "dizziness": "kizunguzungu",
    "cramps": "mikakamao",
    "bruising": "michubuko",
    "obesity": "unene kupita kiasi",
    "swollen legs": "miguu iliyovimba",
    "swollen blood vessels": "mishipa ya damu iliyovimba",
    "puffy face and eyes": "uso na macho yenye uvimbe",
    "enlarged thyroid": "tezi dume iliyovimba",
    "brittle nails": "kucha dhaifu",
    "swollen extremeties": "viungo vilivyovimba",
    "excessive hunger": "njaa kupita kiasi",
    "extra marital contacts": "mahusiano nje ya ndoa",
    "drying and tingling lips": "midomo mikavu na hisi ya kuwashwa",
    "slurred speech": "matamshi yasiyoeleweka",
    "knee pain": "maumivu ya magoti",
    "hip joint pain": "maumivu ya nyonga",
    "muscle weakness": "udhaifu wa misuli",
    "stiff neck": "shingo ngumu",
    "swelling joints": "uvimbe kwenye viungo",
    "movement stiffness": "ukakamavu wa mwili",
    "spinning movements": "kuhisi dunia inazunguka",
    "loss of balance": "kupoteza mlingano",
    "unsteadiness": "kutotulia",
    "weakness of one body side": "udhaifu wa upande mmoja wa mwili",
    "loss of smell": "kupoteza uwezo wa kunusa",
    "bladder discomfort": "usumbufu wa kibofu",
    "foul smell of urine": "harufu mbaya ya mkojo",
    "continuous feel of urine": "hisia ya haja ndogo kila wakati",
    "passage of gases": "kupitisha gesi",
    "internal itching": "mwasho wa ndani",
    "toxic look (typhos)": "muonekano wa sumu (typhos)",
    "depression": "msongo wa mawazo",
    "irritability": "hasira za haraka",
    "muscle pain": "maumivu ya misuli",
    "altered sensorium": "mabadiliko ya ufahamu",
    "red spots over body": "madoadoa mekundu mwilini",
    "belly pain": "maumivu ya tumbo",
    "abnormal menstruation": "hedhi isiyo ya kawaida",
    "dischromic patches": "madoa ya rangi isiyo ya kawaida",
    "watering from eyes": "machozi kutoka machoni",
    "increased appetite": "kuongezeka kwa hamu ya kula",
    "polyuria": "mkojo mwingi",
    "family history": "historia ya familia",
    "mucoid sputum": "makoo yenye ute",
    "rusty sputum": "makoo yenye kutu",
    "lack of concentration": "ukosefu wa umakini",
    "visual disturbances": "usumbufu wa kuona",
    "receiving blood transfusion": "kupokea damu ya kuongezewa",
    "receiving unsterile injections": "kupokea sindano zisizo safi",
    "coma": "koma",
    "stomach bleeding": "kutokwa na damu tumboni",
    "distention of abdomen": "kuvimba kwa tumbo",
    "history of alcohol consumption": "historia ya unywaji pombe",
    "fluid overload.1": "kujaa kwa maji mwilini",
    "blood in sputum": "damu kwenye makoo",
    "prominent veins on calf": "mishipa inayoonekana kwenye ndama",
    "palpitations": "mapigo ya moyo yasiyo ya kawaida",
    "painful walking": "maumivu wakati wa kutembea",
    "pus filled pimples": "vipele vyenye usaha",
    "blackheads": "vipele vyeusi",
    "scurring": "kovu",
    "skin peeling": "ngozi inayochunika",
    "silver like dusting": "vumbi kama fedha",
    "small dents in nails": "mashimo madogo kwenye kucha",
    "inflammatory nails": "kucha zilizo na uchochezi",
    "blister": "malengelenge",
    "red sore around nose": "kidonda chekundu karibu na pua",
    "yellow crust ooze": "mafuta ya manjano yanayotoka"
}

def update_symptoms(request):
    # Fetch all symptom records
    symptoms = Symptom.objects.all()

    # Iterate over each symptom and update its Swahili translation
    for symptom in symptoms:
        english_name = symptom.name.replace('_', ' ')  # Convert 'joint_pain' -> 'joint pain'
        swahili_translation = symptom_translation.get(english_name, "swahili")  # Get Swahili translation

        # Update the symptom entry
        symptom.name = english_name  # Update the name to have spaces
        symptom.swahili_name = swahili_translation  # Set Swahili translation
        symptom.save()  # Save changes to the database

    return HttpResponse("Symptoms updated successfully!")
