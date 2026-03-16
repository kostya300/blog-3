from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image
from django.urls import reverse
from services.utils import unique_slugify
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
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True,unique=True)
    email = models.EmailField(max_length=254, unique=True, null=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    bio = models.TextField(max_length=500, blank=True)
    profession = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/%Y/%m/%d/',
        default='default.jpg',
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
        ]
    )
    class Meta:
        ordering = ('user',)
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.user.username,self.slug)
        super().save(*args, **kwargs)

        try:
            img = Image.open(self.avatar.path)

            if img.height > 100 or img.width > 100:
                new_img = (100, 100)
                img.thumbnail(new_img)
                img.save(self.avatar.path)
        except FileNotFoundError:
            print(f"Файл {self.avatar.path} не найден. Используется аватар по умолчанию.")
    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        """
        Ссылка на профиль
        """
        return reverse('accounts:users-profile', kwargs={'slug': self.slug})