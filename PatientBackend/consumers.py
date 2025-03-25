from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from authApp.models import CustomUser
import json

# Shared dictionary to track online users
online_users = {}

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract user_id from the URL
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Fetch the user object from the database
        self.user = await self.get_user(self.user_id)
        
        if self.user and self.user.is_authenticated:
            # Add user to the online users list
            online_users[self.user.id] = {
                'username': self.user.username,
                'channel_name': self.channel_name,
            }

            # Create a unique room name for the user
            self.room_name = f'user_{self.user.id}'
            self.room_group_name = f'call_{self.room_name}'

            # Join the room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Accept the WebSocket connection
            await self.accept()

            # Notify all users about the updated online list
            await self.notify_online_users()
        else:
            # Reject the connection if the user is not authenticated
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.is_authenticated:
            # Remove the user from the online users list
            if self.user.id in online_users:
                del online_users[self.user.id]

            # Notify all users about the updated online list
            await self.notify_online_users()

            # Leave the room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def notify_online_users(self):
        """
        Broadcast the updated online users list to all connected users.
        """
        await self.channel_layer.group_send(
            'online_users',
            {
                'type': 'online_users',
                'users': list(online_users.values()),
            }
        )

    async def online_users(self, event):
        """
        Send the updated online users list to the client.
        """
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': event['users'],
        }))

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        """
        data = json.loads(text_data)
        
        if data.get('type') == 'call_request':
            # Handle call request
            target_user_id = data['target_user_id']
            await self.channel_layer.group_send(
                f'call_user_{target_user_id}',
                {
                    'type': 'call_request',
                    'caller_id': self.user.id,
                    'caller_username': self.user.username,
                }
            )
        
        elif data.get('type') == 'call_response':
            # Handle call response (accept/reject)
            caller_id = data['caller_id']
            await self.channel_layer.group_send(
                f'call_user_{caller_id}',
                {
                    'type': 'call_response',
                    'target_user_id': self.user.id,
                    'accepted': data['accepted'],
                }
            )
        
        elif data.get('type') == 'ice_candidate':
            # Handle ICE candidate exchange
            target_user_id = data['target_user_id']
            await self.channel_layer.group_send(
                f'call_user_{target_user_id}',
                {
                    'type': 'ice_candidate',
                    'candidate': data['candidate'],
                }
            )
        
        elif data.get('type') == 'offer':
            # Handle WebRTC offer
            target_user_id = data['target_user_id']
            await self.channel_layer.group_send(
                f'call_user_{target_user_id}',
                {
                    'type': 'offer',
                    'offer': data['offer'],
                }
            )
        
        elif data.get('type') == 'answer':
            # Handle WebRTC answer
            target_user_id = data['target_user_id']
            await self.channel_layer.group_send(
                f'call_user_{target_user_id}',
                {
                    'type': 'answer',
                    'answer': data['answer'],
                }
            )

    async def call_request(self, event):
        """
        Send a call request to the target user.
        """
        await self.send(text_data=json.dumps({
            'type': 'call_request',
            'caller_id': event['caller_id'],
            'caller_username': event['caller_username'],
        }))

    async def call_response(self, event):
        """
        Send a call response (accept/reject) to the caller.
        """
        await self.send(text_data=json.dumps({
            'type': 'call_response',
            'target_user_id': event['target_user_id'],
            'accepted': event['accepted'],
        }))

    async def ice_candidate(self, event):
        """
        Send an ICE candidate to the target user.
        """
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate'],
        }))

    async def offer(self, event):
        """
        Send a WebRTC offer to the target user.
        """
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'offer': event['offer'],
        }))

    async def answer(self, event):
        """
        Send a WebRTC answer to the target user.
        """
        await self.send(text_data=json.dumps({
            'type': 'answer',
            'answer': event['answer'],
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        """
        Fetch the user object from the database.
        """
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None