from .models import Post
from django import template
from .forms import SearchForm, SubscribeForm
from django.db.models import Count
from taggit.models import Tag
def popular_posts(request):
    popular_posts = Post.published.annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count')[:5]
    return {'popular_posts': popular_posts}
def most_viewed_posts(request):
    return {
        'most_viewed_posts': Post.published.order_by('-views')[:5]
    }
def search_form(request):
    return {'search_form': SearchForm()}

def categories(request):
    return {
        'categories': Post.published.values('category__title', 'category__slug').distinct()
    }
def subscribe_form(request):
    return {'subscribe_form': SubscribeForm()}

import requests

def weather_context(request):
    access_key = '5b263cd9-9216-441d-8920-286359af7072'
    headers = {"X-Yandex-Weather-Key": access_key}

    query = """
    {
        weatherByPoint(request: { lat: 56.8389, lon: 60.6057 }) {
            now {
                temperature
            }
        }
    }
    """

    try:
        response = requests.post(
            'https://api.weather.yandex.ru/graphql/query',
            headers=headers,
            json={'query': query},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            temperature = data['data']['weatherByPoint']['now']['temperature']
            return {'weather_temperature': temperature}
    except Exception:
        pass

    return {'weather_temperature': None}

# --- НОВАЯ ФУНКЦИЯ ДЛЯ ТЁМНОЙ/СВЕТЛОЙ ТЕМЫ ---
def theme_context(request):
    # По умолчанию — светлая тема
    theme = request.COOKIES.get('theme','light')
    return {'current_theme': theme}