import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Mark previous messages as read immediately upon connection
        await self.mark_messages_as_read(self.room_id, self.user)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat_message')

        if msg_type == 'chat_message':
            # ... (Existing logic, but also handle file_url if present)
            message = data.get('message', '')
            user_id = data['user_id']
            reply_to = data.get('reply_to', None)
            file_url = data.get('file_url', None)
            is_media = data.get('is_media', False)
            timestamp_str = data.get('timestamp', None)
            sender_timezone = data.get('timezone', 'UTC')

            # Parse timestamp if provided
            if timestamp_str:
                try:
                    timestamp = timezone.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = timezone.now()
            else:
                timestamp = timezone.now()

            # If it's a text message, save it. If it has file_url, it was already saved in views.py
            if not file_url:
                await self.save_message(user_id, self.room_id, message, reply_to, timestamp)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user_id': user_id,
                    'reply_to': reply_to,
                    'file_url': file_url,
                    'is_media': is_media,
                    'timestamp': timestamp.isoformat(),
                    'timezone': sender_timezone
                }
            )
        
        elif msg_type == 'mark_read':
            # Broadcast read receipt
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'read_receipt', 'reader_id': data['user_id']}
            )

        elif msg_type == 'delete_message':
            # Handle message deletion
            message_id = data.get('message_id')
            user_id = data.get('user_id')
            
            # Verify ownership and delete
            deleted = await self.delete_message(message_id, user_id)
            
            # Broadcast deletion to all clients in the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id,
                    'deleted': deleted,
                    'user_id': user_id
                }
            )

        elif msg_type == 'call_signal':
            # ... (Existing Call Logic) ...
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_signal',
                    'sender_id': data['user_id'],
                    'payload': data['payload'],
                    'signal_type': data['signal_type']
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def send_signal(self, event):
        await self.send(text_data=json.dumps(event))
        
    async def read_receipt(self, event):
        await self.send(text_data=json.dumps(event))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, user_id, room_id, text, reply_to_id=None, timestamp=None):
        user = User.objects.get(id=user_id)
        conversation = Conversation.objects.get(id=room_id)
        reply_obj = None
        if reply_to_id:
            try:
                reply_obj = Message.objects.get(id=reply_to_id)
            except: pass
        
        if timestamp:
            Message.objects.create(sender=user, conversation=conversation, text=text, reply_to=reply_obj, timestamp=timestamp)
        else:
            Message.objects.create(sender=user, conversation=conversation, text=text, reply_to=reply_obj)

    @database_sync_to_async
    def mark_messages_as_read(self, room_id, user):
        # Mark all messages NOT sent by me as read
        if user.is_authenticated:
            Conversation.objects.get(id=room_id).messages.exclude(sender=user).update(is_read=True)

    @database_sync_to_async
    def delete_message(self, message_id, user_id):
        """Soft-delete message if user is the sender"""
        try:
            message = Message.objects.get(id=message_id)
            # Only allow sender to delete their own message
            if str(message.sender.id) == str(user_id):
                message.text = "[Message deleted]"
                message.save()
                return True
            return False
        except Message.DoesNotExist:
            return False