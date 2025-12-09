from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    # We disable the default 'username' validation to allow flexible inputs if needed,
    # but we will still use the field for the unique handle (e.g., @cool_dev).
    email = models.EmailField(_('email address'), unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    dob = models.DateField(null=True, blank=True)
    
    # These fields are required for the "Passwordless" logic
    is_mobile_verified = models.BooleanField(default=False)
    
    # We will use 'mobile' as the primary login identifier internally, 
    # but our custom login logic will handle Email OR Mobile.
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['email', 'username']

    def __str__(self):
        return self.username