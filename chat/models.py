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

class Group(models.Model):
    """
    Represents a group chat with multiple members.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_groups")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="chat_groups")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ('-updated_at',)
    
    def __str__(self):
        return self.name

class Channel(models.Model):
    """
    Represents a broadcast channel - one-to-many communication.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_channels")
    subscribers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="subscribed_channels")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    
    class Meta:
        ordering = ('-updated_at',)
    
    def __str__(self):
        return self.name

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name="messages", blank=True, null=True)
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name="messages", blank=True, null=True)
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, related_name="messages", blank=True, null=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="message_sender")
    text = models.TextField(blank=True)
    
    # Media/Files
    attachment = models.FileField(upload_to='uploads/', blank=True, null=True)
    is_media = models.BooleanField(default=False) # True if image/video
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Features
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_forwarded = models.BooleanField(default=False)
    
    # Read Status
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ('timestamp',)