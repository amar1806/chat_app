from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='chat_dashboard'),
    
    # --- HTMX PARTIALS (2nd Column Lists) ---
    path('partial/list/chats/', views.chat_list_partial, name='list_chats'),
    path('partial/list/channels/', views.channels_list_partial, name='list_channels'),
    path('partial/list/calls/', views.calls_list_partial, name='list_calls'),
    path('partial/list/status/', views.status_list_partial, name='list_status'),

    # --- HTMX PARTIALS (3rd Column Content) ---
    path('get-chat/<uuid:room_id>/', views.get_chat_content, name='get_chat_content'),
    path('profile/<int:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('settings/', views.settings_page, name='settings_page'),
    
    # --- MISSING PAGES (The Fix for your Error) ---
    path('channels/', views.channels_page, name='channels_page'),
    path('status/', views.status_page, name='status_page'),
    path('calls/', views.calls_page, name='calls_page'),

    # --- CONTACTS & ACTIONS ---
    path('contacts/', views.contacts_page, name='contacts_page'),
    path('start-contact/<int:contact_id>/', views.start_chat_from_contact, name='start_contact'),
    path('start-group-member/<int:target_user_id>/', views.start_chat_from_group_member, name='start_chat_from_group_member'),
    path('add-contact/', views.add_contact, name='add_contact'),
]