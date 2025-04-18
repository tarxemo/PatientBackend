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
            if hasattr(self, 'room_group_name'):
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
        
        if data.get('action') == 'call':
            # Handle incoming call request
            target_username = data['target']
            target_user = await self.get_user_by_username(target_username)
            if target_user:
                await self.channel_layer.group_send(
                    f'call_user_{target_user.id}',
                    {
                        'type': 'incoming_call',
                        'from': self.user.username,
                        'offer': data['offer'],
                    }
                )

        elif data.get('action') == 'answer':
            # Handle answering a call
            target_user_id = data['target_user_id']
            await self.channel_layer.group_send(
                f'call_user_{target_user_id}',
                {
                    'type': 'call_answered',
                }
            )

        elif data.get('action') == 'ice_candidate':
            # Handle ICE candidate exchange
            target_user_id = data['to']
            target_user = await self.get_user_by_username(target_user_id)
            if target_user:
                await self.channel_layer.group_send(
                    f'call_user_{target_user.id}',
                    {
                        'type': 'ice_candidate',
                        'candidate': data['candidate'],
                    }
                )

    async def incoming_call(self, event):
        """
        Send an incoming call notification to the recipient.
        """
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'from': event['from'],
            'offer': event['offer']
        }))

    async def call_answered(self, event):
        """
        Send a call answered notification.
        """
        await self.send(text_data=json.dumps({
            'type': 'call_answered',
        }))

    async def ice_candidate(self, event):
        """
        Send an ICE candidate to the target user.
        """
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate'],
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

    @database_sync_to_async
    def get_user_by_username(self, username):
        """
        Fetch the user object from the database by username.
        """
        try:
            return CustomUser.objects.filter(username=username).first()
        except CustomUser.DoesNotExist:
            return None
