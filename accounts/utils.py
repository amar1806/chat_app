import random
from django.core.cache import cache # This uses Redis!

def generate_otp(identifier):
    """Generates a 6-digit OTP and stores it in Redis for 5 minutes."""
    otp = str(random.randint(100000, 999999))
    # Key example: "otp_user_9876543210"
    cache.set(f'otp_user_{identifier}', otp, timeout=300)
    print(f"DEBUG: OTP for {identifier} is {otp}") # Look at console for the code
    return otp

def verify_otp_logic(identifier, user_otp):
    """Checks if the OTP matches the one in Redis."""
    stored_otp = cache.get(f'otp_user_{identifier}')
    if stored_otp and stored_otp == user_otp:
        return True
    return False