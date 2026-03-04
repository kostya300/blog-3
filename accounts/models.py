from django.contrib.auth.models import User
from django.db import models
from PIL import Image
# Если нужны дополнительные поля, создайте профиль
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.user.username
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=254, unique=True, null=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    bio = models.TextField(max_length=500, blank=True)
    profession = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        default='default.jpg',
        blank=True
    )
    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        try:
            img = Image.open(self.avatar.path)

            if img.height > 100 or img.width > 100:
                new_img = (100, 100)
                img.thumbnail(new_img)
                img.save(self.avatar.path)
        except FileNotFoundError:
            print(f"Файл {self.avatar.path} не найден. Используется аватар по умолчанию.")
