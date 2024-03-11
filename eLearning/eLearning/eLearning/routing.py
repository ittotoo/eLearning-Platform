from django.urls import re_path, path
from Main.consumers import *

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<course_id>\w+)/$', ChatConsumer.as_asgi()),
]