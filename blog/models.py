import os
from PIL import Image
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from pathlib import Path

def validate_image_file(image):
    # 1. Проверка расширения
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    file_extension = Path(image.name).suffix.lower()  # Используем image.name вместо image.filename

    if file_extension not in allowed_extensions:
        raise ValidationError(
            f'Недопустимое расширение файла. Разрешены: {", ".join(allowed_extensions)}'
        )

    # 2. Проверка размера (максимум 5 МБ)
    max_size = 5 * 1024 * 1024  # 5 МБ в байтах
    if image.size > max_size:
        raise ValidationError('Размер файла не должен превышать 5 МБ.')

    # 3. Проверка типа содержимого через Pillow
    try:
        with Image.open(image) as img:
            img.verify()  # Проверяет целостность файла

        # Повторная загрузка для получения информации о формате
        with Image.open(image) as img:
            if img.format.lower() not in ['jpeg', 'png', 'webp']:
                raise ValidationError('Файл не является корректным изображением.')
    except (IOError, SyntaxError):
        raise ValidationError('Загруженный файл не является корректным изображением или повреждён.')

class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='blog_posts'
    )
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )
    image = models.ImageField(
        upload_to='images/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Загрузите изображение (максимум 5 МБ, поддерживаемые форматы: JPG, PNG, WEBP)',
        validators=[validate_image_file]
    )

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def __str__(self):
        return self.title
