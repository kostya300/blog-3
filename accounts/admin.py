from django.contrib import admin
from accounts.models import Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Админ-панель модели профиля
    """
    list_display = ('user', 'slug', 'email')
    list_display_links = ('user', 'slug')
