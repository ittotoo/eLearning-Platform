import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()

# Defines a WebSocket consumer for handling real-time chat functionality.
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extracts the course_id from the URL route and constructs a unique group name.
        self.room_name = self.scope['url_route']['kwargs']['course_id']
        self.room_group_name = f'chat_{self.room_name}'

        # Asynchronously adds the current channel to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accepts the WebSocket connection.
        await self.accept()

    async def disconnect(self, close_code):
        # Asynchronously removes the channel from the group upon disconnecting.
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Handles receiving messages from WebSocket clients.
    async def receive(self, text_data):
        # Deserializes the text data into JSON.
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Retrieves the username of the sender, defaulting to 'Anonymous' if unauthenticated.
        user = self.scope["user"]
        username = user.get_username() if user.is_authenticated else 'Anonymous'
        user_id = str(user.id) if user.is_authenticated else 'Anonymous'        

        # Sends the message to the group, including the sender's username and ID.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'user_id': str(user_id),    # Include the username in the event
            }
        )

    # Handles messages sent to the group from any user's channel.
    async def chat_message(self, event):
        # Extracts message content and sender details from the event.
        message = event['message']
        username = event.get('username', 'Anonymous')  # Fallback to 'Anonymous' if username is not provided.
        user_id = event['user_id']

        # Sends the message data to the WebSocket client, including the sender's username.
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'user_id': user_id,
        }))
