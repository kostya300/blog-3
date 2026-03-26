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
from ckeditor.fields import RichTextField


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

    title = RichTextField(config_name='awesome_ckeditor', verbose_name='Краткое описание', max_length=500)
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
    body = RichTextField(config_name='awesome_ckeditor', verbose_name='Полный текст записи')
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

    def get_sum_rating(self):
        from django.db.models import Sum
        result = self.ratings.aggregate(Sum('value'))['value__sum']
        return result or 0

    def get_likes_count(self):
        return self.ratings.filter(value=1).count()

    def get_dislikes_count(self):
        return self.ratings.filter(value=-1).count()
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
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Rating(models.Model):
    """
    Модель рейтинга: Лайк - Дизлайк
    """
    post = models.ForeignKey(to=Post, verbose_name='Запись', on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(to=User, verbose_name='Пользователь', on_delete=models.CASCADE, blank=True, null=True)
    value = models.IntegerField(verbose_name='Значение', choices=[(1, 'Нравится'), (-1, 'Не нравится')])
    time_create = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)
    ip_address = models.GenericIPAddressField(verbose_name='IP Адрес')

    class Meta:
        unique_together = ('post', 'ip_address')
        ordering = ('-time_create',)
        indexes = [models.Index(fields=['-time_create', 'value'])]
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'

    def __str__(self):
        return self.post.title

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
