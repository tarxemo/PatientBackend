
from patient.models import Doctor, LabTech, Patient


def handle_user_profile(user, user_type, profile_data=None):
    """
    Handles creation or update of profile objects based on user_type
    """
    print(profile_data)
    profile_data = profile_data or {}
    
    # Delete any existing profile that doesn't match the current user_type
    if hasattr(user, 'doctor_profile') and user_type != 'doctor':
        Doctor.objects.filter(user=user).delete()
    if hasattr(user, 'patient_profile') and user_type != 'patient':
        Patient.objects.filter(user=user).delete()
    if hasattr(user, 'labtech_profile') and user_type != 'lab_technician':
        LabTech.objects.filter(user=user).delete()
    
    # Create or update the appropriate profile
    if user_type == 'doctor':
        doctor, created = Doctor.objects.get_or_create(user=user)
        for field, value in profile_data.items():
            if hasattr(doctor, field) and value is not None:
                setattr(doctor, field, value)
        doctor.save()
        return doctor
    
    elif user_type == 'patient':
        patient, created = Patient.objects.get_or_create(user=user)
        for field, value in profile_data.items():
            if hasattr(patient, field) and value is not None:
                setattr(patient, field, value)
        patient.save()
        return patient
    
    elif user_type == 'lab_technician':
        labtech, created = LabTech.objects.get_or_create(user=user)
        for field, value in profile_data.items():
            if hasattr(labtech, field) and value is not None:
                setattr(labtech, field, value)
        labtech.save()
        return labtech
    
    return None