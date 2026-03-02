from django import template

register = template.Library()

@register.filter
def add_css(field, css_classes):
    """Добавляет CSS‑классы к виджету поля формы."""
    return field.as_widget(attrs={"class": css_classes})
