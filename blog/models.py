import os
from PIL import Image
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from pathlib import Path
from django.urls import reverse
from taggit.managers import TaggableManager
from mptt.models import MPTTModel, TreeForeignKey
from services .utils import unique_slugify

def validate_image_file(file):
    # Проверка расширения
    if not file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise ValidationError('Недопустимое расширение файла')

    # Проверка размера (5 МБ = 5 * 1024 * 1024 байт)
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError('Размер файла не должен превышать 5 МБ')
    # Проверка, что файл — корректное изображение
    try:
        img = Image.open(file)
        img.verify()
    except (IOError, SyntaxError):
        raise ValidationError('не является корректным изображением или повреждён')


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Category(MPTTModel):
    """
        Модель категорий с вложенностью
    """
    title = models.CharField(max_length=255, verbose_name='Название категории')
    slug = models.SlugField(max_length=255, verbose_name='URL категории', blank=True)
    description = models.TextField(verbose_name='Описание категории', max_length=300)
    parent = TreeForeignKey(
        to='self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name='children',
        verbose_name='Родительская категория'
    )

    class MPTTMeta:
        """
            Сортировка по вложенности
        """
        order_insertion_by = ('title',)

    class Meta:
        """
            Название модели в админ панели, таблица с данными
        """
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'app_categories'

    def __str__(self):
        """
            Возвращение заголовка категории
        """
        return self.title

class PostManager(models.Manager):
    """
        Кастомный менеджер для модели постов
    """

    def get_queryset(self):
        """
        Список постов (SQL запрос с фильтрацией по статусу опубликованно)
        """
        return super().get_queryset().filter(status='published')
class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True)
    category = TreeForeignKey(
        to='Category',
        on_delete=models.PROTECT,
        related_name='posts',
        verbose_name='Категория',
        default=None,  # или удалите default
        null=True  # если допустимо отсутствие категории
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='blog_posts'
    )
    body = models.TextField()
    views = models.PositiveIntegerField(default=0)
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
    objects = models.Manager()
    custom = PostManager()
    published = PublishedManager()
    tags = TaggableManager()

    class Meta:
        db_table = 'blog_post'
        ordering = ['-publish', '-created']
        indexes = [
            models.Index(fields=['-publish', '-created', 'status'], ),
        ]
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def get_absolute_url(self):
        """
                Получаем прямую ссылку на статью
                """
        return reverse('blog:post_detail', args=[self.publish.year, self.publish.month, self.publish.day, self.slug])
    def save(self, *args, **kwargs):
        """
            При сохранении генерируем слаг и проверяем на уникальность
        """
        self.slug = unique_slugify(self, self.title,self.slug)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.PROTECT, related_name='comments')
    name = models.CharField(max_length=80)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='comments')
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.post}'
