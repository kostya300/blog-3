from .models import Post
from django.db.models import Count

def popular_posts(request):
    popular_posts = Post.published.annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count')[:5]
    return {'popular_posts': popular_posts}