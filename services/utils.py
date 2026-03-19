from django.utils.text import slugify
from unidecode import unidecode
import re

def unique_slugify(instance, title, slug_field=None):
    """
    Генерирует уникальный slug из заголовка.
    """
    # Определяем, откуда брать текст для slug
    if slug_field is None:
        slug = slugify(unidecode(title))
    else:
        slug = slugify(unidecode(slug_field))

    # Очищаем от всех недопустимых символов (оставляем только a-z, 0-9, -)
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Получаем модель текущего экземпляра
    model = instance.__class__

    # Сохраняем оригинальный slug для генерации вариантов
    original_slug = slug
    counter = 1

    # Проверяем, существует ли уже такой slug
    while model.objects.filter(slug=slug).exists():
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug