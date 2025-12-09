from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.auth_page, name='auth_home'),
    path('logout/', views.logout_view, name='logout'),
    
    # JSON APIs
    path('api/send-otp/', views.api_send_otp, name='api_send_otp'),
    path('api/verify-otp/', views.api_verify_otp, name='api_verify_otp'),
    path('api/create-user/', views.api_complete_profile, name='api_complete_profile'),
    path('api/login-user/', views.api_login_success, name='api_login_success'),

]