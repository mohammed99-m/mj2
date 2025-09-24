from django.urls import path
from .views import  list_services , api_send_message4,contact_page,add_service_with_video

urlpatterns = [
   path('services/',list_services,name="get all Services"),
   ##path('addservice/', add_service, name='add service'),
   path('addservice_with_video/', add_service_with_video, name='add service'),
   # path('send-email/', send_email_view, name='send email'),
   # path('send-test-email/', send_test_email, name='send email'),
   # path('send-test2-email/', send_test2_email, name='send email2'),
   # path('send-to-marko-safe/', send_to_marko_safe , name='send with safe'),
   path("api/send-message/",api_send_message4, name="api_send_message"),
   path("contact/",contact_page, name="api_send_message"),
]