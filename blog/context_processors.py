from .models import Post
from django import template
from .forms import SearchForm
from django.db.models import Count
from taggit.models import Tag
def popular_posts(request):
    popular_posts = Post.published.annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count')[:5]
    return {'popular_posts': popular_posts}
def search_form(request):
    return {'search_form': SearchForm()}

# register = template.Library()
# @register.inclusion_tag('blog/post/includes/tag_cloud.html')
# def show_tag_cloud(count=20):
#     tags = Tag.objects.annotate(
#         post_count=Count('taggit_taggeditem_items')
#     ).filter(post_count__gt=0).order_by('-post_count')[:count]
#     return {'tags': tags}