from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Conversation, Message, Contact

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
    Shared logic to fetch and filter conversations.
    Used by both the dashboard (initial load) and chat_list_partial (search/refresh).
    """
    user = request.user
    query = request.GET.get('search', '')
    
    if query:
        # Search by username or mobile
        conversations = Conversation.objects.filter(
            Q(initiator=user) | Q(receiver=user)
        ).filter(
            Q(initiator__username__icontains=query) | 
            Q(receiver__username__icontains=query) 
        ).distinct()
    else:
        conversations = Conversation.objects.filter(
            Q(initiator=user) | Q(receiver=user)
        ).select_related('initiator', 'receiver')

    chat_data = []
    for chat in conversations:
        other_user = chat.receiver if chat.initiator == user else chat.initiator
        last_msg = chat.messages.last()
        display_name = get_display_name(user, other_user)
        
        chat_data.append({
            'id': chat.id,
            'other_user': other_user,
            'display_name': display_name,
            'preview': last_msg.text if last_msg else "New connection",
            'timestamp': last_msg.timestamp if last_msg else chat.start_time,
        })
    
    chat_data.sort(key=lambda x: x['timestamp'], reverse=True)
    return {'chat_list': chat_data}

# --- MAIN DASHBOARD ---

@login_required(login_url='/auth/')
def dashboard(request):
    """
    Renders the main application shell.
    Initial chat list is passed to populate the 2nd column immediately.
    """
    context = get_chat_list_context(request)
    return render(request, 'chat/dashboard.html', context)

# --- 2ND COLUMN PARTIALS (Contextual Lists) ---

@login_required
def chat_list_partial(request):
    """Returns just the list of chats. Used for Search and Tab Switching."""
    context = get_chat_list_context(request)
    return render(request, 'chat/partials/list_chats.html', context)

@login_required
def channels_list_partial(request):
    """Returns the list of channels."""
    return render(request, 'chat/partials/list_channels.html')

@login_required
def calls_list_partial(request):
    """Returns the list of calls."""
    return render(request, 'chat/partials/list_calls.html')

@login_required
def status_list_partial(request):
    """Returns the list of status updates."""
    return render(request, 'chat/partials/list_status.html')

# --- 3RD COLUMN / MAIN STAGE CONTENT ---

@login_required
def get_chat_content(request, room_id):
    """Renders the Chat Interface."""
    chat = get_object_or_404(Conversation, id=room_id)
    
    # Security check
    if request.user != chat.initiator and request.user != chat.receiver:
        return HttpResponseForbidden()

    other_user = chat.receiver if chat.initiator == request.user else chat.initiator
    
    # Fetch messages with reply context
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
    """
    Renders the Full Profile Page into the main stage.
    """
    target_user = get_object_or_404(User, id=user_id)
    is_contact = Contact.objects.filter(owner=request.user, saved_user=target_user).exists()
    display_name = get_display_name(request.user, target_user)
    
    context = {
        'target_user': target_user,
        'display_name': display_name,
        'is_contact': is_contact,
        'media_count': 0, 
    }
    return render(request, 'chat/partials/profile_full.html', context)

@login_required
def settings_page(request):
    """Renders the Settings Menu."""
    return render(request, 'chat/partials/settings.html', {'user': request.user})

@login_required
def contacts_page(request):
    """Renders the 'New Chat' contact selection screen."""
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
    """Starts or retrieves a conversation with a saved contact."""
    contact = get_object_or_404(Contact, id=contact_id, owner=request.user)
    target_user = contact.saved_user
    
    chat = Conversation.objects.filter(
        Q(initiator=request.user, receiver=target_user) | 
        Q(initiator=target_user, receiver=request.user)
    ).first()

    if not chat:
        chat = Conversation.objects.create(initiator=request.user, receiver=target_user)
    
    # Return the chat content directly to open it immediately
    return get_chat_content(request, chat.id)

@login_required
def start_chat_from_group_member(request, target_user_id):
    """
    Starts a chat from a Group Member list (Bypasses Contact Check).
    This was the MISSING function causing your error.
    """
    target_user = get_object_or_404(User, id=target_user_id)
    
    chat = Conversation.objects.filter(
        Q(initiator=request.user, receiver=target_user) | 
        Q(initiator=target_user, receiver=request.user)
    ).first()

    if not chat:
        chat = Conversation.objects.create(initiator=request.user, receiver=target_user)

    return get_chat_content(request, chat.id)

@login_required
def add_contact(request):
    """Handles adding a new contact."""
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

# --- PLACEHOLDER PAGES (Required for Sidebar Links) ---

@login_required
def channels_page(request):
    """Renders the Channels list placeholder."""
    return render(request, 'chat/partials/placeholder.html', {'title': 'Channels', 'icon': 'fas fa-bullhorn'})

@login_required
def status_page(request):
    """Renders the Status updates placeholder."""
    return render(request, 'chat/partials/placeholder.html', {'title': 'Status', 'icon': 'far fa-dot-circle'})

@login_required
def calls_page(request):
    """Renders the Calls history placeholder."""
    return render(request, 'chat/partials/placeholder.html', {'title': 'Calls', 'icon': 'fas fa-phone-alt'})