import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.db.models import Q
from authApp.models import CustomUser
from patient.models import Consultation, Disease, Doctor, Patient, Symptom

from asgiref.sync import sync_to_async

@sync_to_async
def get_user_by_id(user_id):
    return CustomUser.objects.get(id=user_id)

@sync_to_async
def get_disease_by_name(name):
    return Disease.objects.get(name=name)

@sync_to_async
def get_matched_symptoms(transcribed_text):
    return list(Symptom.objects.filter(
        Q(name__icontains=transcribed_text) | Q(swahili_name__icontains=transcribed_text)
    ))

@sync_to_async
def create_consultation(caller_id, doctor_username, disease, matched_symptoms):
    consultation = Consultation.objects.create(
        patient=Patient.objects.get(user__id=caller_id),
        doctor=Doctor.objects.get(user__username=doctor_username),
        disease=disease
    )
    consultation.symptoms.set(matched_symptoms)
    consultation.save()
    return consultation

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_group_name = f"user_{self.user.id}"

        # Join the user's group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"User {self.user.username} connected")

    async def disconnect(self, close_code):
        # Leave the user's group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"User {self.user.username} disconnected")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        print(f"Received action: {action} from user {self.user.username}")

        # Handle different actions
        if action == "call":
            await self.initiate_call(data)
        elif action == "accept":
            await self.accept_call(data)
        elif action == "reject":
            await self.reject_call(data)
        elif action == "offer":
            print(f"Forwarding offer to user {data.get('target_user')}")
            await self.forward_signal(data, "offer")
        elif action == "answer":
            print(f"Forwarding answer to user {data.get('caller_id')}")
            await self.forward_signal(data, "answer")
        elif action == "ice_candidate":
            print(f"Forwarding ICE candidate to user {data.get('target_user')}")
            await self.forward_signal(data, "ice_candidate")
        else:
            print(f"Unknown action: {action}")

    async def initiate_call(self, data):
        target_user_id = data["target_user"]
        print(f"User {self.user.username} is calling user {target_user_id}")

        await self.channel_layer.group_send(
            f"user_{target_user_id}",
            {
                "type": "call_request",
                "caller_id": self.user.id,
                "caller_name": self.user.username,
            }
        )

    async def call_request(self, event):
        await self.send(text_data=json.dumps({
            "action": "incoming_call",
            "caller_id": event["caller_id"],
            "caller_name": event["caller_name"],
        }))

    async def accept_call(self, data):
        caller_id = data["caller_id"]
        print(f"User {self.user.username} accepted call from {caller_id}")
        
        caller_user = await get_user_by_id(caller_id)

        diagnosis_state = cache.get(f'diagnosis_{caller_user.username}')
        if not diagnosis_state:
            print("Diagnosis session not found.")
            return

        transcribed_text = diagnosis_state.get("transcribed_text", "")
        top_disease_name = diagnosis_state.get("current_predictions", [None])[0]
        if not top_disease_name:
            print("No predicted disease found.")
            return

        try:
            disease = await get_disease_by_name(top_disease_name)
        except Disease.DoesNotExist:
            print(f"Disease {top_disease_name} not found.")
            return

        matched_symptoms = await get_matched_symptoms(transcribed_text)
        await create_consultation(caller_id, self.user.username, disease, matched_symptoms)

        await self.channel_layer.group_send(
            f"user_{caller_id}",
            {
                "type": "call_accepted",
                "callee_id": self.user.id,
                "callee_name": self.user.username,
            }
        )



    async def call_accepted(self, event):
        await self.send(text_data=json.dumps({
            "action": "call_accepted",
            "callee_id": event["callee_id"],
            "callee_name": event["callee_name"],
        }))

    async def reject_call(self, data):
        caller_id = data["caller_id"]
        print(f"User {self.user.username} rejected call from {caller_id}")

        await self.channel_layer.group_send(
            f"user_{caller_id}",
            {
                "type": "call_rejected",
            }
        )

    async def call_rejected(self, event):
        await self.send(text_data=json.dumps({
            "action": "call_rejected",
        }))

    async def forward_signal(self, data, action):
        target_id = data.get("target_user") or data.get("caller_id")
        print(f"Forwarding {action} to user {target_id}")

        await self.channel_layer.group_send(
            f"user_{target_id}",
            {"type": action, **data}
        )

    async def offer(self, event):
        await self.send(text_data=json.dumps(event))

    async def answer(self, event):
        await self.send(text_data=json.dumps(event))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps(event))