from urllib import request
from django.db.models import Count, F, Prefetch
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .forms import EmailPostForm, CommentForm, SearchForm, PostCreateForm, PostUpdateForm, CommentCreateForm
from .models import Post, Category, Comment, Like, CommentLike
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Sum
from django.db.models import Count, F
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .utils import get_comment_word
from django.views import View

from blog.model_loader import generate_response
from django.views.decorators.csrf import csrf_exempt
import json


def llama_chat_view(request):
    """Страница чата с LLM"""
    return render(request, 'blog/llm/chat.html')


# """LLaMA API view starts here"""
@csrf_exempt
@require_POST
def llama_api(request):
    """API endpoint для генерации текста"""
    try:
        data = json.loads(request.body)
        user_input = data.get("message", "").strip()

        if not user_input:
            return JsonResponse({"error": "Пустой запрос"}, status=400)

        # Генерация ответа
        response_text = generate_response(user_input, max_length=300)
        if not response_text.strip():
            response_text = "Извините, я не могу сгенерировать ответ."
        return JsonResponse({
            "response": response_text
        })


    except json.JSONDecodeError:

        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    except Exception as e:

        print("Ошибка генерации:", str(e))  # Лог в консоль

        return JsonResponse({"error": "Ошибка модели: " + str(e)}, status=500)


# """LLaMA API view ends here"""

# Главная страница на основе класса
class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'blog/post/list.html'
    paginate_by = 3

    def get_queryset(self):
        # Начинаем с published
        queryset = Post.published.annotate(
            likes_count=Count('likes')
        )

        # Если пользователь авторизован — добавляем информацию о его лайках
        if self.request.user.is_authenticated:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'likes',
                    queryset=Like.objects.filter(user=self.request.user),
                    to_attr='user_liked'
                )
            )

        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags=tag)
            self.tag = tag
        else:
            self.tag = None

        return queryset  # <-- Конец get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['categories'] = Category.objects.all()

        # Популярные посты
        context['popular_posts'] = Post.published.annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count')[:5]

        # Самые просматриваемые
        context['most_viewed_posts'] = Post.published.order_by('-views')[:5]

        return context
@require_POST
@login_required
def toggle_comment_like(request):
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, id=comment_id)

    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    likes_count = comment.comment_likes.count()

    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })
@require_POST
@login_required
def toggle_like(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        # Если уже лайкал — удаляем (отменяем лайк)
        like.delete()
        liked = False
    else:
        liked = True
    likes_count = post.likes.count()
    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })


class PostUpdateView(UpdateView):
    """
    Представление: обновления материала на сайте
    """
    model = Post
    template_name = 'blog/post/post_update.html'
    context_object_name = 'post'
    form_class = PostUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Обновление статьи: {self.object.title}'
        return context

    def form_valid(self, form):
        return super().form_valid(form)


class PostCreateView(CreateView):
    """
    Представление: создание материалов на сайте
    """
    model = Post
    template_name = 'blog/post/post_create.html'
    form_class = PostCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление статьи на сайт'
        return context

    def form_invalid(self, form):
        form.instance.author = self.request.user
        return super().form_invalid(form)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        queryset = Post.published.all()
        return get_object_or_404(
            queryset,
            slug=self.kwargs['slug'],
            publish__year=self.kwargs['year'],
            publish__month=self.kwargs['month'],
            publish__day=self.kwargs['day'],
            status=Post.Status.PUBLISHED,
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        Post.objects.filter(id=self.object.id).update(views=F('views') + 1)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        # Добавляем, ставил ли текущий пользователь лайк
        # Лайк поста
        if self.request.user.is_authenticated:
            context['user_liked'] = post.likes.filter(user=self.request.user).exists()
        else:
            context['user_liked'] = False

        # Комментарии и их лайки
        root_comments = post.comments.filter(active=True, parent__isnull=True).prefetch_related(
            Prefetch(
                'children',
                queryset = Comment.objects.filter(active=True),
                to_attr = 'children_comments'
            )
        )
        # Аннотируем количество лайков и факт лайка текущим пользователем
        for comment in root_comments:
            comment.likes_count = comment.comment_likes.count()
            if self.request.user.is_authenticated:
                comment.user_liked = comment.comment_likes.filter(user=self.request.user).exists()
            else:
                comment.user_liked = False

            for child in comment.children_comments:
                child.likes_count = child.comment_likes.count()  # ✅ Есть
                if self.request.user.is_authenticated:
                    child.user_liked = child.comment_likes.filter(user=self.request.user).exists()  # ✅ Есть
                else:
                    child.user_liked = False

        total_comments = post.comments.filter(active=True).count()
        post_tags_ids = post.tags.values_list('id', flat=True)
        similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
        similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
        comment_word = get_comment_word(total_comments)
        context['post'] = self.object
        context.update({
            'comments': root_comments,
            'form': CommentForm(),
            'similar_posts': similar_posts,
            'total_comments': total_comments,
            'comment_word': comment_word,
            'current_user': self.request.user,
            'categories': Category.objects.all(),
            'popular_posts': Post.published.annotate(comment_count=Count('comments')).order_by('-comment_count')[:5],
            'most_viewed_posts': Post.published.order_by('-views')[:5],
        })
        return context


def post_list_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    post_list = Post.published.filter(category=category)
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    popular_posts = Post.published.annotate(comment_count=Count('comments')).order_by('-comment_count')[:5]
    most_viewed_posts = Post.published.order_by('-views')[:5]

    return render(
        request,
        'blog/post/list.html',
        {
            'posts': posts,
            'tag': None,
            'popular_posts': popular_posts,
            'most_viewed_posts': most_viewed_posts,
            'categories': Category.objects.all(),
            'current_category': category,
        },
    )


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', 'body')
            search_query = SearchQuery(query)
            results = Post.published.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(search=search_query).order_by('-rank')

    return render(request, 'blog/post/search.html', {
        'form': form,
        'query': query,
        'results': results
    })


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n{cd['name']}'s ({cd['email']}) comments: {cd['comments']}"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [cd['to']])
            sent = True
    else:
        form = EmailPostForm()

    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})


def comment_create(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentCreateForm(request.POST, post=post, user=request.user)
        if form.is_valid():
            comment = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'comment_id': comment.id})
            return redirect(post.get_absolute_url())
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    return redirect(post.get_absolute_url())


@require_POST
def post_comment(request, post_id):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
        return redirect(
            'blog:post_detail',
            year=post.publish.year,
            month=post.publish.month,
            day=post.publish.day,
            slug=post.slug,
        )
    return render(request, 'blog/post/includes/comment_form.html',
                  {'post': post, 'form': form, 'comment': None})


def about(request):
    return render(request, 'blog/post/about.html')


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

    popular_posts = Post.published.annotate(comment_count=Count('comments')).order_by('-comment_count')[:5]

    return render(request, 'blog/post/travel.html', {
        'posts': posts,
        'popular_posts': popular_posts
    })
