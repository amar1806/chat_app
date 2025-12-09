import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # --- RECEIVE FROM FRONTEND ---
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat_message')

        # 1. CHAT MESSAGES
        if msg_type == 'chat_message':
            message = data['message']
            user_id = data['user_id']
            reply_to = data.get('reply_to', None)

            # Save to DB
            await self.save_message(user_id, self.room_id, message, reply_to)

            # Broadcast to Group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user_id': user_id,
                    'reply_to': reply_to
                }
            )
        
        # 2. CALL SIGNALS (WebRTC)
        elif msg_type == 'call_signal':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_signal',
                    'sender_id': data['user_id'],
                    'payload': data['payload'],
                    'signal_type': data['signal_type']
                }
            )

    # --- SEND TO FRONTEND ---
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user_id': event['user_id'],
            'reply_to': event.get('reply_to')
        }))

    async def send_signal(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_signal',
            'sender_id': event['sender_id'],
            'payload': event['payload'],
            'signal_type': event['signal_type']
        }))

    # --- DATABASE ---
    @database_sync_to_async
    def save_message(self, user_id, room_id, text, reply_to_id=None):
        user = User.objects.get(id=user_id)
        conversation = Conversation.objects.get(id=room_id)
        reply_obj = None
        if reply_to_id:
            try:
                reply_obj = Message.objects.get(id=reply_to_id)
            except Message.DoesNotExist:
                pass
                
        Message.objects.create(sender=user, conversation=conversation, text=text, reply_to=reply_obj)