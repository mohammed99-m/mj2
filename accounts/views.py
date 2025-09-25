import cloudinary
from django.shortcuts import render
from rest_framework.decorators import api_view
from .serializers import ServiceSerializer
from .models import Service
from rest_framework import status
from rest_framework.response import Response
# Create your views here.


@api_view(["GET"])
def list_services(request):
    services = Service.objects.all()  
    serializer = ServiceSerializer(services,many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import ServiceSerializer

@api_view(["POST"])
def add_service_with_video(request):
    data = request.data.copy()

    # Instead of uploading, get URLs from request if provided
    image_url = data.get("image_url")
    video_url = data.get("video_url")

    if image_url:
        data['image_url'] = image_url
    else:
        data['image_url'] = ""

    if video_url:
        data['video_url'] = video_url
    else:
        data['video_url'] = ""

    serializer = ServiceSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



import json
import re
import logging

from django.conf import settings
from django.core.mail import EmailMessage, BadHeaderError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from .models import UserMessage

logger = logging.getLogger(__name__)

HEADER_INJECTION_RE = re.compile(r'[\r\n]')
MAX_NAME_LEN = 120
MAX_EMAIL_LEN = 254
MAX_MESSAGE_LEN = 5000


@ensure_csrf_cookie
@csrf_protect
def contact_page(request):
    """
    - GET: يعرض صفحة التواصل contact.html + يرسل كوكي csrftoken
    - POST (Form): يعالج بيانات الفورم ويرسل الإيميل
    """
    if request.method == "GET":
        return render(request, "contact.html")

    if request.method == "POST":
        data = {
            "user_name": request.POST.get("user_name", ""),
            "user_email": request.POST.get("user_email", ""),
            "message": request.POST.get("message", ""),
        }
        return _process_contact_data(request, data)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_protect
def api_send_message4(request):
    """
    - POST (JSON/AJAX): يعالج البيانات القادمة من الموبايل أو الواجهة الأمامية
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    data = {
        "user_name": payload.get("user_name", ""),
        "user_email": payload.get("user_email", ""),
        "message": payload.get("message", ""),
    }
    return _process_contact_data(request, data)


def _process_contact_data(request, data):
    """
    دالة مشتركة: تحقق من المدخلات + تخزين + إرسال إيميل
    """
    raw_name = (data.get("user_name") or "").strip()
    raw_email = (data.get("user_email") or "").strip()
    raw_message = (data.get("message") or "").strip()

    if not raw_message:
        return _response_by_request_type(request, {"error": "Message cannot be empty."}, status=400)

    if len(raw_name) > MAX_NAME_LEN or len(raw_email) > MAX_EMAIL_LEN or len(raw_message) > MAX_MESSAGE_LEN:
        return _response_by_request_type(request, {"error": "One of the fields is too long."}, status=400)

    for val in (raw_name, raw_email):
        if HEADER_INJECTION_RE.search(val):
            return _response_by_request_type(request, {"error": "Invalid characters in input."}, status=400)

    try:
        validate_email(raw_email)
    except ValidationError:
        return _response_by_request_type(request, {"error": "Invalid email address."}, status=400)

    safe_name = escape(raw_name)
    safe_message = escape(raw_message)

    try:
        UserMessage.objects.create(
            user_name=safe_name,
            user_email=raw_email,
            message=safe_message
        )
    except Exception as e:
        logger.exception("Failed to save UserMessage")
        return _response_by_request_type(request, {"error": "Failed to save message."}, status=500)

    subject = f"رسالة من {raw_name or 'مستخدم مجهول'}"
    full_message = f"رسالة من: {raw_name} <{raw_email}>\n\n{raw_message}"

    try:
        email = EmailMessage(
              subject=subject,
              body=full_message,
              from_email=settings.EMAIL_HOST_USER,   # البريد المرسل منه
              to=[settings.ADMIN_EMAIL],             # البريد المستلم (حدد في settings.py)
              reply_to=[raw_email],                  # البريد الذي يرد عليه
)
        email.send(fail_silently=False)
    except BadHeaderError:
        return _response_by_request_type(request, {"error": "Invalid header found."}, status=400)
    except Exception:
        logger.exception("Failed to send email")
        return _response_by_request_type(request, {"error": "Failed to send email."}, status=500)

    return _response_by_request_type(request, {"status": "Message sent successfully."}, status=200)


def _response_by_request_type(request, payload, status=200):
    """
    يرجع JSON لو الطلب AJAX/JSON
    ويرجع HTML لو كان من فورم عادي
    """
    if request.content_type == "application/json" or "application/json" in request.META.get("HTTP_ACCEPT", ""):
        return JsonResponse(payload, status=status)

    if status == 200:
        return render(request, "contact.html", {"success": payload.get("status", "")})
    else:
        return render(request, "contact.html", {"error": payload.get("error", "")}, status=status)


#############################################################################################################

from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(["POST"])
def send_email_view(request):
    subject = request.data.get("subject", "No subject")
    message = request.data.get("message", "No message")
    recipient = request.data.get("to", "someone@example.com")
    me = request.data.get("to", "someone@example.com")
    try:
        send_mail(
            subject,
            message,
            me,  # From
            [recipient],             # To
            fail_silently=False,
        )
        return JsonResponse({"success": True, "msg": "Email sent!"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    


from django.core.mail import send_mail
from django.http import HttpResponse

def send_test_email(request):
    subject = "تجربة إرسال بريد من Django"
    message = "مرحبًا! هذا البريد تم إرساله من Django باستخدام Gmail."
    from_email = "md393911@gmail.com@gmail.com"
    recipient_list = ["markoriobrazil@gmail.com"]  # ضع بريد المستلم هنا

    send_mail(subject, message, from_email, recipient_list)
    return HttpResponse("تم إرسال البريد بنجاح!")


# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # فقط المستخدمين المسجلين
def send_test_email(request):
    subject = request.data.get("subject")
    message = request.data.get("message")
    recipient = request.data.get("recipient")

    send_mail(subject, message, request.user.email, [recipient])
    return Response({"status": "Email sent!"})



# views.py with oute secure
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
import json

@csrf_exempt
def send_test2_email(request):
    if request.method == "POST":
        data = json.loads(request.body)
        subject = data.get("subject")
        message = data.get("message")
        recipient = data.get("recipient")

        send_mail(
            subject,
            message,
            "markoriobrazil@gmail.com",  # ضع بريدك هنا
            [recipient]
        )
        return JsonResponse({"status": "Email sent!"}) 
    return JsonResponse({"error": "Invalid method"}, status=400)


### last email

# views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
import json

@csrf_exempt
def send_to_marko(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_name = data.get("user_name")        # اسم المستخدم أو بريده
        user_email = data.get("user_email")      # بريد المستخدم (اختياري)
        message_content = data.get("message")    # محتوى الرسالة

        # نجمع رسالة المستخدم مع معلوماته
        full_message = f"رسالة من: {user_name} ({user_email})\n\n{message_content}"

        send_mail(
            subject=f"رسالة من {user_name}",
            message=full_message,
            from_email="nehadshretah@gmail.com",       # بريد النظام المرسل
            recipient_list=["markoriobrazil@gmail.com"]  # بريد marko المستلم
        )
        return JsonResponse({"status": "Email sent to Marko!"})
    
    return JsonResponse({"error": "Invalid method"}, status=400)



from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.html import escape
import json
from .models import UserMessage

@csrf_protect
def send_to_marko_safe(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_name = escape(data.get("user_name", "Anonymous"))
            user_email = escape(data.get("user_email", ""))
            message_content = escape(data.get("message", ""))

            if not message_content:
                return JsonResponse({"error": "Message cannot be empty."}, status=400)

            # حفظ الرسالة في قاعدة البيانات
            UserMessage.objects.create(
                user_name=user_name,
                user_email=user_email,
                message=message_content
            )

            # إرسال البريد إلى Marko
            full_message = f"رسالة من: {user_name} ({user_email})\n\n{message_content}"

            send_mail(
                subject=f"رسالة من {user_name}",
                message=full_message,
                from_email="nehadshretah@gmail.com",       # بريد النظام
                recipient_list=["markoriobrazil@gmail.com"]
            )

            return JsonResponse({"status": "Email sent to Marko safely!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

    return JsonResponse({"error": "Invalid method"}, status=400)




import json
import re
import logging

from django.conf import settings
from django.core.mail import EmailMessage, BadHeaderError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from .models import UserMessage

logger = logging.getLogger(__name__)

HEADER_INJECTION_RE = re.compile(r'[\r\n]')
MAX_NAME_LEN = 120
MAX_EMAIL_LEN = 254
MAX_MESSAGE_LEN = 5000

@csrf_protect
def contact_page(request):
    """
    Render HTML contact page (GET) and accept form POST (regular form).
    """
    if request.method == "GET":
        return render(request, "contact.html")  # template below

    # If POST from a normal form (not JSON), process below by delegating to same logic
    # We will call the shared function below
    if request.method == "POST":
        # form fields are in request.POST
        data = {
            "user_name": request.POST.get("user_name", ""),
            "user_email": request.POST.get("user_email", ""),
            "message": request.POST.get("message", ""),
        }
        return _process_contact_data(request, data)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_protect
def api_send_message(request):
    """
    Accept JSON POSTs (AJAX / mobile) to send message.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    data = {
        "user_name": payload.get("user_name", ""),
        "user_email": payload.get("user_email", ""),
        "message": payload.get("message", ""),
    }
    return _process_contact_data(request, data)


# def _process_contact_data(request, data):
#     """
#     Shared validation + save + send logic.
#     Returns JsonResponse (for API) or renders template with context (for form).
#     """
#     raw_name = (data.get("user_name") or "").strip()
#     raw_email = (data.get("user_email") or "").strip()
#     raw_message = (data.get("message") or "").strip()

#     # Basic validation
#     if not raw_message:
#         return _response_by_request_type(request, {"error": "Message cannot be empty."}, status=400)

#     if len(raw_name) > MAX_NAME_LEN or len(raw_email) > MAX_EMAIL_LEN or len(raw_message) > MAX_MESSAGE_LEN:
#         return _response_by_request_type(request, {"error": "One of the fields is too long."}, status=400)

#     # Prevent header injection in name and email
#     for val in (raw_name, raw_email):
#         if HEADER_INJECTION_RE.search(val):
#             return _response_by_request_type(request, {"error": "Invalid characters in input."}, status=400)

#     # Validate email format
#     try:
#         validate_email(raw_email)
#     except ValidationError:
#         return _response_by_request_type(request, {"error": "Invalid email address."}, status=400)

#     # Escape for safe HTML rendering; we keep raw_email as stored to allow contact later
#     safe_name = escape(raw_name)
#     safe_message = escape(raw_message)

#     # Save to DB
#     try:
#         UserMessage.objects.create(
#             user_name=safe_name,
#             user_email=raw_email,
#             message=safe_message
#         )
#     except Exception as e:
#         logger.exception("Failed to save UserMessage")
#         return _response_by_request_type(request, {"error": "Failed to save message."}, status=500)

#     # Prepare email
#     subject = f"رسالة من {raw_name or 'مستخدم مجهول'}"
#     full_message = f"رسالة من: {raw_name} <{raw_email}>\n\n{raw_message}"

#     try:
#         email = EmailMessage(
#             subject=subject,
#             body=full_message,
#             from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
#             to=[getattr(settings, "ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)],
#             reply_to=[raw_email],
#         )
#         email.send(fail_silently=False)
#     except BadHeaderError:
#         return _response_by_request_type(request, {"error": "Invalid header found."}, status=400)
#     except Exception as e:
#         logger.exception("Failed to send email")
#         return _response_by_request_type(request, {"error": "Failed to send email."}, status=500)

#     return _response_by_request_type(request, {"status": "Message sent successfully."}, status=200)


def _response_by_request_type(request, payload, status=200):
    """
    If the request is AJAX/JSON we return JsonResponse, otherwise render template or redirect.
    """
    # If the original request had JSON body or Accept header asks for JSON -> JSON
    if request.content_type == "application/json" or request.META.get("HTTP_ACCEPT", "").find("application/json") != -1:
        return JsonResponse(payload, status=status)
    # Otherwise render the contact page with success/error message
    if status == 200:
        return render(request, "contact.html", {"success": payload.get("status", "")})
    else:
        return render(request, "contact.html", {"error": payload.get("error", "")}, status=status)
    