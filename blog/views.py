from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from django.conf import settings
from .forms import EmailPostForm,CommentForm
from .models import Post
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count, F


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags=tag)
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    popular_posts = Post.published.annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count')[:5]
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts,
                   'tag': tag,'popular_posts': popular_posts})


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
@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)
        # Назначить пост комментарию
        comment.post = post
        # Сохранить комментарий в базе данных
        comment.save()

        return redirect('blog:post_detail',
                    year=post.publish.year,
                    month=post.publish.month,
                    day=post.publish.day,
                    slug=post.slug)
    return render(request, 'blog/post/includes/comment_form.html',
                  {'post': post, 'form': form, 'comment': None})

def post_detail(request, year, month, day, slug):

    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=slug, publish__year=year, publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids) \
        .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    Post.objects.filter(id=post.id).update(views=F('views') + 1)
    return render(request, 'blog/post/detail.html', {'post': post,'comments': comments, 'form': form, 'similar_posts': similar_posts})


def about(request):
    return render(request, 'blog/post/about.html')


def login(request):
    return render(request, 'blog/users/login.html')
def travel(request):
    post_list = Post.published.all()
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    popular_posts = Post.published.annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count')[:5]

    return render(request,'blog/post/travel.html',{'posts': posts,
                   'popular_posts': popular_posts})