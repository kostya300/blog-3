from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from rest_framework.authtoken.models import Token
@receiver(post_save, sender=User)
def create_profile(sender,instance,created ,**kwargs):
    if created:
        Profile.objects.create(user=instance,
                               phone_number=None)
        Token.objects.create(user=instance)
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при сохранении аккаунта"""
    instance.profile.save()