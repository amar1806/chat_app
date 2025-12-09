from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='chat_dashboard'),
    path('chat/', views.dashboard, name='chat_route'),  # Redirect /chat/ to dashboard
    
    # --- HTMX PARTIALS (2nd Column Lists) ---
    path('partial/list/chats/', views.chat_list_partial, name='list_chats'),
    path('partial/list/channels/', views.channels_list_partial, name='list_channels'),
    path('partial/list/calls/', views.calls_list_partial, name='list_calls'),
    path('partial/list/status/', views.status_list_partial, name='list_status'),

    # --- HTMX PARTIALS (3rd Column Content) ---
    path('get-chat/<uuid:room_id>/', views.get_chat_content, name='get_chat_content'),
    path('get-group/<uuid:group_id>/', views.get_group_content, name='get_group_content'),
    path('get-channel/<uuid:channel_id>/', views.get_channel_content, name='get_channel_content'),
    path('profile/<int:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('settings/', views.settings_page, name='settings_page'),
    
    # --- PAGES ---
    path('groups/', views.groups_page, name='groups_page'),
    path('channels/', views.channels_page, name='channels_page'),
    path('status/', views.status_page, name='status_page'),
    path('calls/', views.calls_page, name='calls_page'),
    path('contacts/', views.contacts_page, name='contacts_page'),

    # --- GROUP ACTIONS ---
    path('group/create/', views.create_group, name='create_group'),
    path('group/delete/<uuid:group_id>/', views.delete_group, name='delete_group'),

    # --- CHANNEL ACTIONS ---
    path('channel/create/', views.create_channel, name='create_channel'),
    path('channel/subscribe/<uuid:channel_id>/', views.subscribe_channel, name='subscribe_channel'),
    path('channel/unsubscribe/<uuid:channel_id>/', views.unsubscribe_channel, name='unsubscribe_channel'),
    path('channel/delete/<uuid:channel_id>/', views.delete_channel, name='delete_channel'),

    # --- CONTACT ACTIONS ---
    path('start-contact/<int:contact_id>/', views.start_chat_from_contact, name='start_contact'),
    path('start-group-member/<int:target_user_id>/', views.start_chat_from_group_member, name='start_chat_from_group_member'),
    path('add-contact/', views.add_contact, name='add_contact'),
    path('api/save-contact/', views.save_contact_api, name='save_contact_api'),

    # --- MESSAGE ACTIONS ---
    path('api/delete-message/', views.delete_message, name='delete_message'),
    path('api/forward-message/', views.forward_message, name='forward_message'),
    path('api/bulk-delete-messages/', views.bulk_delete_messages, name='bulk_delete_messages'),
    path('api/bulk-forward-messages/', views.bulk_forward_messages, name='bulk_forward_messages'),
    path('api/delete-chat/<uuid:chat_id>/', views.delete_chat, name='delete_chat'),

    # FILE UPLOAD
    path('api/upload/', views.upload_attachment, name='upload_attachment'),
]