from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

def verify_credentials(email, password):
    if not email or not password:
        return False, None

    user = authenticate(username=email, password=password)
    if user is None:
        return False, None
    return True, user
