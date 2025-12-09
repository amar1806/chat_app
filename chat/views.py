from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Conversation, Message, Contact, Group, Channel
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

User = get_user_model()

# --- HELPER FUNCTIONS ---

def get_display_name(owner, target_user):
    """Returns saved contact name if exists, else mobile/username."""
    try:
        contact = Contact.objects.get(owner=owner, saved_user=target_user)
        return contact.name
    except Contact.DoesNotExist:
        return target_user.mobile if hasattr(target_user, 'mobile') and target_user.mobile else target_user.username

def get_chat_list_context(request):
    """
    Advanced Search Logic:
    1. Finds existing chats matching query (Username/Mobile).
    2. Finds saved contacts matching query (Name/Mobile).
    3. Merges them so you can start chats with contacts directly from search.
    """
    user = request.user
    query = request.GET.get('search', '').strip()
    
    chat_data = []
    
    if query:
        # A. Find Contacts matching Name or Mobile
        contacts = Contact.objects.filter(
            Q(owner=user) & 
            (Q(name__icontains=query) | Q(saved_user__mobile__icontains=query))
        ).select_related('saved_user')
        
        # B. Find Chats matching Username or Mobile
        conversations = Conversation.objects.filter(
            Q(initiator=user) | Q(receiver=user)
        ).filter(
            Q(initiator__username__icontains=query) | 
            Q(receiver__username__icontains=query) |
            Q(initiator__mobile__icontains=query) | 
            Q(receiver__mobile__icontains=query)
        ).select_related('initiator', 'receiver').prefetch_related('messages')

        # Track IDs to avoid duplicates
        processed_ids = set()

        # 1. Add Matching Conversations
        for chat in conversations:
            other_user = chat.receiver if chat.initiator == user else chat.initiator
            processed_ids.add(other_user.id)
            
            last_msg = chat.messages.last()
            display_name = get_display_name(user, other_user)
            
            chat_data.append({
                'type': 'chat',
                'id': chat.id,
                'display_name': display_name,
                'preview': last_msg.text if last_msg else "Active Chat",
                'timestamp': last_msg.timestamp if last_msg else chat.start_time,
            })

        # 2. Add Matching Contacts (Who don't have a chat yet)
        for contact in contacts:
            target_user = contact.saved_user
            
            # Only add if we didn't already add a chat for this user
            if target_user.id not in processed_ids:
                chat_data.append({
                    'type': 'contact',
                    'id': contact.id, # Contact ID (used to start chat)
                    'display_name': contact.name,
                    'preview': f"Mobile: {target_user.mobile}",
                    'timestamp': None, # No time yet
                })
                processed_ids.add(target_user.id)

    else:
        # Default: Show all existing conversations
        conversations = Conversation.objects.filter(
            Q(initiator=user) | Q(receiver=user)
        ).select_related('initiator', 'receiver').prefetch_related('messages')

        for chat in conversations:
            other_user = chat.receiver if chat.initiator == user else chat.initiator
            last_msg = chat.messages.last()
            display_name = get_display_name(user, other_user)
            
            chat_data.append({
                'type': 'chat',
                'id': chat.id,
                'display_name': display_name,
                'preview': last_msg.text if last_msg else "New connection",
                'timestamp': last_msg.timestamp if last_msg else chat.start_time,
            })
        
        chat_data.sort(key=lambda x: x['timestamp'], reverse=True)

    return {'chat_list': chat_data}

# --- MAIN DASHBOARD ---

@login_required(login_url='/auth/')
def dashboard(request):
    context = get_chat_list_context(request)
    return render(request, 'chat/dashboard.html', context)

# --- 2ND COLUMN PARTIALS ---

@login_required
def chat_list_partial(request):
    context = get_chat_list_context(request)
    return render(request, 'chat/partials/list_chats.html', context)

@login_required
def channels_list_partial(request):
    return render(request, 'chat/partials/list_channels.html')

@login_required
def calls_list_partial(request):
    return render(request, 'chat/partials/list_calls.html')

@login_required
def status_list_partial(request):
    return render(request, 'chat/partials/list_status.html')

# --- 3RD COLUMN CONTENT ---

@login_required
def get_chat_content(request, room_id):
    chat = get_object_or_404(Conversation, id=room_id)
    if request.user != chat.initiator and request.user != chat.receiver:
        return HttpResponseForbidden()

    other_user = chat.receiver if chat.initiator == request.user else chat.initiator
    messages = chat.messages.select_related('reply_to').all()
    is_contact = Contact.objects.filter(owner=request.user, saved_user=other_user).exists()
    display_name = get_display_name(request.user, other_user)

    context = {
        'chat': chat,
        'other_user': other_user,
        'display_name': display_name,
        'is_contact': is_contact,
        'messages': messages,
    }
    return render(request, 'chat/partials/chat_content.html', context)

@login_required
def get_user_profile(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    is_contact = Contact.objects.filter(owner=request.user, saved_user=target_user).exists()
    display_name = get_display_name(request.user, target_user)
    
    context = {
        'target_user': target_user,
        'display_name': display_name,
        'is_contact': is_contact,
    }
    return render(request, 'chat/partials/profile_full.html', context)

@login_required
def settings_page(request):
    return render(request, 'chat/partials/settings.html', {'user': request.user})

@login_required
def contacts_page(request):
    user = request.user
    query = request.GET.get('search', '')
    if query:
        contacts = Contact.objects.filter(
            Q(owner=user) & 
            (Q(name__icontains=query) | Q(saved_user__mobile__icontains=query))
        ).select_related('saved_user')
    else:
        contacts = Contact.objects.filter(owner=user).select_related('saved_user')
    return render(request, 'chat/contacts.html', {'contacts': contacts, 'search_query': query})

# --- ACTIONS ---

@login_required
def start_chat_from_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, owner=request.user)
    target_user = contact.saved_user
    chat = Conversation.objects.filter(
        Q(initiator=request.user, receiver=target_user) | 
        Q(initiator=target_user, receiver=request.user)
    ).first()

    if not chat:
        chat = Conversation.objects.create(initiator=request.user, receiver=target_user)
    
    return get_chat_content(request, chat.id)

@login_required
def start_chat_from_group_member(request, target_user_id):
    target_user = get_object_or_404(User, id=target_user_id)
    chat = Conversation.objects.filter(
        Q(initiator=request.user, receiver=target_user) | 
        Q(initiator=target_user, receiver=request.user)
    ).first()
    if not chat:
        chat = Conversation.objects.create(initiator=request.user, receiver=target_user)
    return get_chat_content(request, chat.id)

# --- FILE UPLOAD HANDLER ---
@login_required
@csrf_exempt # In production, handle CSRF properly via JS headers
def upload_attachment(request):
    if request.method == "POST" and request.FILES.get('file'):
        file = request.FILES['file']
        room_id = request.POST.get('room_id')
        user_id = request.POST.get('user_id')
        
        # 1. Save Message directly
        chat = Conversation.objects.get(id=room_id)
        sender = User.objects.get(id=user_id)
        
        # Check if image
        is_image = file.content_type.startswith('image')
        
        msg = Message.objects.create(
            conversation=chat,
            sender=sender,
            attachment=file,
            is_media=is_image,
            text=file.name # Show filename as text fallback
        )
        
        # 2. Return URL to JS so it can send it via WebSocket
        return JsonResponse({
            'status': 'ok',
            'file_url': msg.attachment.url,
            'is_media': is_image,
            'message_id': str(msg.id),
            'filename': file.name
        })
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def add_contact(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        name = request.POST.get('name')
        if not mobile or not name:
            messages.error(request, "Name and Mobile required.")
            return redirect('chat_dashboard')
        try:
            target_user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            messages.error(request, "Number not registered.")
            return redirect('chat_dashboard')
        if target_user == request.user:
            messages.error(request, "Cannot add yourself.")
            return redirect('chat_dashboard')
        if not Contact.objects.filter(owner=request.user, saved_user=target_user).exists():
            Contact.objects.create(owner=request.user, saved_user=target_user, name=name)
            messages.success(request, "Contact saved.")
        return redirect('chat_dashboard')
    return redirect('chat_dashboard')

@login_required
def save_contact_api(request):
    """API endpoint to save a contact from chat view"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            contact_user_id = data.get('contact_user_id')
            contact_name = data.get('contact_name', '').strip()
            
            if not contact_user_id or not contact_name:
                return JsonResponse({'success': False, 'error': 'Missing contact details'}, status=400)
            
            try:
                target_user = User.objects.get(id=contact_user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
            
            if target_user == request.user:
                return JsonResponse({'success': False, 'error': 'Cannot add yourself'}, status=400)
            
            # Create or update contact
            contact, created = Contact.objects.get_or_create(
                owner=request.user,
                saved_user=target_user,
                defaults={'name': contact_name}
            )
            
            if not created:
                contact.name = contact_name
                contact.save()
            
            return JsonResponse({'success': True, 'message': 'Contact saved successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

# --- GROUP VIEWS ---

@login_required
def groups_page(request):
    """List all groups for the user"""
    user_groups = request.user.groups.all().prefetch_related('messages')
    context = {
        'groups': user_groups,
    }
    return render(request, 'chat/groups.html', context)

@login_required
def get_group_content(request, group_id):
    """Get group chat content"""
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all() and request.user != group.creator:
        return HttpResponseForbidden()
    
    messages_list = group.messages.select_related('sender', 'reply_to').all()
    context = {
        'group': group,
        'messages': messages_list,
        'members': group.members.all(),
    }
    return render(request, 'chat/partials/group_content.html', context)

@login_required
def create_group(request):
    """Create a new group"""
    if request.method == "POST":
        group_name = request.POST.get('name')
        description = request.POST.get('description', '')
        member_ids = request.POST.getlist('members')
        
        if not group_name:
            messages.error(request, "Group name is required")
            return redirect('groups_page')
        
        group = Group.objects.create(
            name=group_name,
            description=description,
            creator=request.user
        )
        group.members.add(request.user)  # Add creator
        
        # Add selected members
        if member_ids:
            group.members.add(*member_ids)
        
        messages.success(request, f"Group '{group_name}' created successfully")
        return redirect('groups_page')
    
    # Get all contacts for selection
    contacts = Contact.objects.filter(owner=request.user).select_related('saved_user')
    context = {'contacts': contacts}
    return render(request, 'chat/create_group.html', context)

@login_required
def delete_group(request, group_id):
    """Delete a group"""
    group = get_object_or_404(Group, id=group_id)
    if request.user != group.creator:
        return HttpResponseForbidden("Only creator can delete group")
    
    group.delete()
    messages.success(request, "Group deleted")
    return redirect('groups_page')

# --- CHANNEL VIEWS ---

@login_required
def channels_page(request):
    """List all channels user is subscribed to"""
    user_channels = request.user.subscribed_channels.all().prefetch_related('messages')
    created_channels = Channel.objects.filter(creator=request.user)
    context = {
        'channels': user_channels,
        'created_channels': created_channels,
    }
    return render(request, 'chat/channels.html', context)

@login_required
def get_channel_content(request, channel_id):
    """Get channel content"""
    channel = get_object_or_404(Channel, id=channel_id)
    
    # Check permissions
    if channel.is_public or request.user in channel.subscribers.all() or request.user == channel.creator:
        messages_list = channel.messages.select_related('sender', 'reply_to').all()
        context = {
            'channel': channel,
            'messages': messages_list,
            'subscribers': channel.subscribers.all(),
            'is_creator': request.user == channel.creator,
        }
        return render(request, 'chat/partials/channel_content.html', context)
    
    return HttpResponseForbidden()

@login_required
def create_channel(request):
    """Create a new channel"""
    if request.method == "POST":
        channel_name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_public = request.POST.get('is_public') == 'on'
        
        if not channel_name:
            messages.error(request, "Channel name is required")
            return redirect('channels_page')
        
        channel = Channel.objects.create(
            name=channel_name,
            description=description,
            creator=request.user,
            is_public=is_public
        )
        channel.subscribers.add(request.user)  # Add creator as subscriber
        
        messages.success(request, f"Channel '{channel_name}' created successfully")
        return redirect('channels_page')
    
    return render(request, 'chat/create_channel.html')

@login_required
def subscribe_channel(request, channel_id):
    """Subscribe to a channel"""
    channel = get_object_or_404(Channel, id=channel_id)
    if not channel.is_public and request.user != channel.creator:
        return HttpResponseForbidden("Cannot subscribe to private channel")
    
    channel.subscribers.add(request.user)
    messages.success(request, f"Subscribed to '{channel.name}'")
    return redirect('channels_page')

@login_required
def unsubscribe_channel(request, channel_id):
    """Unsubscribe from a channel"""
    channel = get_object_or_404(Channel, id=channel_id)
    channel.subscribers.remove(request.user)
    messages.success(request, f"Unsubscribed from '{channel.name}'")
    return redirect('channels_page')

@login_required
def delete_channel(request, channel_id):
    """Delete a channel"""
    channel = get_object_or_404(Channel, id=channel_id)
    if request.user != channel.creator:
        return HttpResponseForbidden("Only creator can delete channel")
    
    channel.delete()
    messages.success(request, "Channel deleted")
    return redirect('channels_page')

# --- MESSAGE ACTIONS ---

@login_required
@csrf_exempt
def delete_message(request):
    """Delete a message"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            
            msg = get_object_or_404(Message, id=message_id)
            
            # Only message sender can delete
            if msg.sender != request.user:
                return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
            
            msg.delete()
            return JsonResponse({'success': True, 'message': 'Message deleted'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def forward_message(request):
    """Forward a message to another chat"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            target_chat_id = data.get('target_chat_id')
            
            msg = get_object_or_404(Message, id=message_id)
            target_chat = get_object_or_404(Conversation, id=target_chat_id)
            
            # Check if user has access to target chat
            if request.user != target_chat.initiator and request.user != target_chat.receiver:
                return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
            
            # Create forwarded message
            forwarded_msg = Message.objects.create(
                conversation=target_chat,
                sender=request.user,
                text=f"[Forwarded]: {msg.text}",
                attachment=msg.attachment if msg.attachment else None,
                is_media=msg.is_media,
                is_forwarded=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Message forwarded',
                'forwarded_message_id': str(forwarded_msg.id)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def delete_chat(request, chat_id):
    """Delete entire conversation"""
    try:
        chat = get_object_or_404(Conversation, id=chat_id)
        
        # Check if user is part of the conversation
        if request.user != chat.initiator and request.user != chat.receiver:
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
        
        # Delete all messages in conversation
        chat.messages.all().delete()
        chat.delete()
        
        return JsonResponse({'success': True, 'message': 'Chat deleted'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def bulk_delete_messages(request):
    """Delete multiple selected messages"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            
            if not message_ids:
                return JsonResponse({'success': False, 'error': 'No messages selected'}, status=400)
            
            # Delete only messages owned by current user
            deleted_count = Message.objects.filter(
                id__in=message_ids,
                sender=request.user
            ).delete()[0]
            
            return JsonResponse({
                'success': True,
                'message': f'{deleted_count} message(s) deleted'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def bulk_forward_messages(request):
    """Forward multiple selected messages"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            target_chat_id = data.get('target_chat_id')
            
            if not message_ids or not target_chat_id:
                return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
            
            target_chat = get_object_or_404(Conversation, id=target_chat_id)
            
            # Check authorization
            if request.user != target_chat.initiator and request.user != target_chat.receiver:
                return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
            
            messages_to_forward = Message.objects.filter(id__in=message_ids)
            forwarded_count = 0
            
            for msg in messages_to_forward:
                forwarded_msg = Message.objects.create(
                    conversation=target_chat,
                    sender=request.user,
                    text=f"[Forwarded]: {msg.text}",
                    attachment=msg.attachment if msg.attachment else None,
                    is_media=msg.is_media,
                    is_forwarded=True
                )
                forwarded_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'{forwarded_count} message(s) forwarded'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

# --- PLACEHOLDERS ---

@login_required
def status_page(request):
    return render(request, 'chat/partials/placeholder.html', {'title': 'Status', 'icon': 'far fa-dot-circle'})

@login_required
def calls_page(request):
    return render(request, 'chat/partials/placeholder.html', {'title': 'Calls', 'icon': 'fas fa-phone-alt'})