from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage
from django.views.generic import ListView

from .models import Post

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'

def post_detail(request, year, month, day, slug):
    post = get_object_or_404(Post,status=Post.Status.PUBLISHED, slug=slug,publish__year=year, publish__month=month, publish__day=day)
    return render(request, 'blog/post/detail.html', {'post': post})
def about(request):
    return render(request,'blog/post/about.html')
def login(request):
    return render(request,'blog/users/login.html')