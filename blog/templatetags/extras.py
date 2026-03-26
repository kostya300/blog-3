from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Позволяет получать значение из словаря по ключу в шаблоне.
    Возвращает 0, если ключ не найден (для числовых значений рейтинга).
    """

    return dictionary.get(key, 0)