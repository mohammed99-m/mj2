from django.urls import path
from .views import  list_services,add_service_with_video,send_normal_message,messages,delete_service,delete_message,register_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [
   path('services/',list_services,name="get all Services"),
   path('messages/',messages,name="get all messages"),
   path('delete_service/<str:service_id>/',delete_service,name="delete_service"),
   path('delete_message/<str:message_id>/',delete_message,name="delete_message"),
   path('addservice_with_video/', add_service_with_video, name='add service'),
   path("send-message/",send_normal_message, name="api_send_message"),
   path('register/', register_view, name='api-register'),
   path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
   path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
   ##path('addservice/', add_service, name='add service'),
   # path('send-email/', send_email_view, name='send email'),
   # path('send-test-email/', send_test_email, name='send email'),
   # path('send-test2-email/', send_test2_email, name='send email2'),
   # path('send-to-marko-safe/', send_to_marko_safe , name='send with safe'),
   ##path("contact/",contact_page, name="api_send_message"),
]