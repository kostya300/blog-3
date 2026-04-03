import os
from PIL import Image
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.urls import reverse
from taggit.managers import TaggableManager  # Исправлен импорт
from mptt.models import MPTTModel, TreeForeignKey
from services.utils import unique_slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.html import strip_tags


# Исправлен импорт


def validate_image_file(file):
    # Проверка расширения
    if not file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise ValidationError('Недопустимое расширение файла')

    # Проверка размера (5 МБ = 5 × 1024 × 1024 байт)
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError('Размер файла не должен превышать 5 МБ')
    # Проверка, что файл — корректное изображение
    try:
        img = Image.open(file)
        img.verify()
    except (IOError, SyntaxError):
        raise ValidationError('не является корректным изображением или повреждён')


def post_image_upload_to(instance, filename):
    """Функция для формирования пути загрузки изображений"""
    return f'images/{instance.publish.year}/{instance.publish.month:02d}/{instance.publish.day:02d}/{filename}'


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Category(MPTTModel):
    title = models.CharField(max_length=255, verbose_name='Название категории')
    slug = models.SlugField(max_length=255, blank=True, unique=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name='children',
        verbose_name='Родительская категория'
    )

    class MPTTMeta:
        order_insertion_by = ['title']

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'app_categories'

    def __str__(self):
        return self.title


class PostManager(models.Manager):
    """Кастомный менеджер для модели постов"""

    def get_queryset(self):
        """Список постов (SQL запрос с фильтрацией по статусу опубликованно)"""
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)  # Исправлено




class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = CKEditor5Field(
        config_name='default',
        verbose_name='Краткое описание',
        max_length=500,
        help_text="Поддерживается форматирование, но избегайте слишком длинных заголовков."
    )
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True)
    category = TreeForeignKey(
        to='Category',
        on_delete=models.PROTECT,
        related_name='posts',
        verbose_name='Категория',
        null=True,
        blank=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='blog_posts'
    )
    body = CKEditor5Field(
        config_name='extends',
        verbose_name='Полный текст записи'
    )
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
        upload_to=post_image_upload_to,  # ← исправлено: используем кастомную функцию
        blank=True,
        null=True,
        help_text='Загрузите изображение (максимум 5 МБ, поддерживаемые форматы: JPG, PNG)',
        validators=[validate_image_file]
    )
    fixed = models.BooleanField(default=False, verbose_name='Исправлено')
    updater = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_posts',
        verbose_name='Кто обновил'
    )
    objects = models.Manager()
    custom = PostManager()
    published = PublishedManager()
    tags = TaggableManager()

    class Meta:
        db_table = 'blog_post'
        ordering = ['-publish', '-created']
        indexes = [
            models.Index(fields=['-publish', '-created', 'status']),
        ]
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[
            self.publish.year, self.publish.month, self.publish.day, self.slug
        ])

    def save(self, *args, **kwargs):
        self.title = strip_tags(self.title)
        if not self.slug:
            self.slug = unique_slugify(self, self.title[:50])  # ограничиваем длину для слага
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey("Comment",on_delete=models.CASCADE,related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'comment')  # Один пользователь — один лайк
        ordering = ['-created_at']


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('post', 'user')  # Один пользователь — один лайк
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
    def __str__(self):
        return f'{self.user.username} + {self.post.title}'
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительский комментарий'
    )
    name = models.CharField(max_length=80)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    email = models.EmailField(blank=True, null=True)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
            models.Index(fields=['parent']),  # важно для производительности
        ]

    def get_children(self):
        """Возвращает все дочерние комментарии"""
        return self.children.filter(active=True)

    def is_parent(self):
        """Проверяет, есть ли у комментария ответы"""
        return self.children.exists()

    def __str__(self):
        if self.parent:
            return f'Ответ от {self.name} к комментарию {self.parent.id}'
        return f'Комментарий от {self.name} на {self.body}'
