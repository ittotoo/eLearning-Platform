from django import template
from Main.models import Notification 

register = template.Library()

@register.simple_tag
def get_unread_notifications_count(user):
    return Notification.objects.filter(recipient=user, read=False).count()

@register.simple_tag
def get_unread_notifications(user):
    return Notification.objects.filter(recipient=user, read=False).order_by('-created_at')
