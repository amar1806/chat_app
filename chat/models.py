from django.db import models
from django.conf import settings
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

class Contact(models.Model):
    """
    Represents a saved contact in a user's phonebook.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contacts")
    saved_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_by")
    name = models.CharField(max_length=100) # The name I saved them as
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner', 'saved_user')

    def __str__(self):
        return f"{self.owner} -> {self.name}"

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    initiator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="convo_starter")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="convo_participant")
    start_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (('initiator', 'receiver'),)

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="message_sender")
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to='uploads/', blank=True, null=True)
    is_media = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # --- NEW FEATURES (Point 10) ---
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_forwarded = models.BooleanField(default=False)

    class Meta:
        ordering = ('timestamp',)