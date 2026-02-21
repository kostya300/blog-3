from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage
from django.views.generic import ListView
from django.core.mail import send_mail
from django.conf import settings
from .forms import EmailPostForm
from .models import Post


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    # Извлечь пост по идентификатору id
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailPostForm(request.POST)

        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s ({cd['email']}) comments: {cd['comments']}"
            send_mail(subject, message, settings.EMAIL_HOST_USER,
                      [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,'sent': sent})


def post_detail(request, year, month, day, slug):
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=slug, publish__year=year, publish__month=month,
                             publish__day=day)
    return render(request, 'blog/post/detail.html', {'post': post})


def about(request):
    return render(request, 'blog/post/about.html')


def login(request):
    return render(request, 'blog/users/login.html')
