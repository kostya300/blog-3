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
from .models import Post, Category, Comment, Rating
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count, F
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction

from django.db.models import Count, F, Q, Sum
from .utils import get_comment_word
from django.http import JsonResponse


# Главная страница на основе класса
class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'blog/post/list.html'
    paginate_by = 3

    def get_queryset(self):
        queryset = Post.published.all()

        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags=tag)
            self.tag = tag
        else:
            self.tag = None
        return queryset.prefetch_related('ratings')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['popular_posts'] = Post.published.annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count')[:5]
        context['most_viewed_posts'] = Post.published.order_by('-views')[:5]
        context['categories'] = Category.objects.all()

        # Получаем все рейтинги для постов на странице
        posts = context["posts"]
        post_ids = [post.id for post in posts]

        ratings = Rating.objects.filter(post_id__in=post_ids).values('post_id').annotate(
            rating_sum=Sum('value'),
            likes=Sum('value', filter=Q(value=1)),
            dislikes=Sum('value', filter=Q(value=-1))
        )

        # Обрабатываем NULL-значения
        for item in ratings:
            item['rating_sum'] = item['rating_sum'] or 0
            item['likes'] = item['likes'] or 0
            item['dislikes'] = item['dislikes'] or 0

        # Преобразуем в словарь для быстрого доступа
        ratings_dict = {item['post_id']: item for item in ratings}

        # Добавляем к каждому посту его рейтинг
        post_ratings = {}
        for post in posts:
            rating_info = ratings_dict.get(post.id, {
                'rating_sum': 0,
                'likes': 0,
                'dislikes': 0
            })
            post_ratings[post.id] = {
                'rating_sum': rating_info['rating_sum'],
                'likes': rating_info['likes'],
                'dislikes': rating_info['dislikes'],
            }

        context['post_ratings'] = post_ratings
        return context


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
        # Расчёт рейтингов для текущего поста
        ratings = post.ratings.aggregate(
            rating_sum=Sum('value'),
            likes=Sum('value', filter=Q(value=1)),
            dislikes=Sum('value', filter=Q(value=-1))
        )
        # Обрабатываем NULL-значения
        rating_info = {
            'rating_sum': ratings['rating_sum'] or 0,
            'likes': ratings['likes'] or 0,
            'dislikes': ratings['dislikes'] or 0,
        }
        root_comments = post.comments.filter(active=True, parent__isnull=True)
        for comment in root_comments:
            comment.children_comments = comment.children.filter(active=True)

        total_comments = post.comments.filter(active=True).count()
        post_tags_ids = post.tags.values_list('id', flat=True)
        similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
        similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
        comment_word = get_comment_word(total_comments)

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
            'post_ratings': {post.id: rating_info}
        })
        return context


class RatingCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        post_id = request.POST.get('post_id')
        value = int(request.POST.get('value'))

        try:
            post = Post.objects.get(id=post_id)
            rating, created = Rating.objects.get_or_create(
                post=post,
                user=request.user,
                defaults={'value': value}
            )

            if not created:
                if rating.value == value:
                    rating.delete()
                else:
                    rating.value = value
                    rating.save()

            # Пересчёт рейтингов после изменения
            ratings = post.ratings.aggregate(
                rating_sum=Sum('value'),
                likes=Sum('value', filter=Q(value=1)),
                dislikes=Sum('value', filter=Q(value=-1))
            )

            return JsonResponse({
                'rating_sum': ratings['rating_sum'] or 0,
                'likes': ratings['likes'] or 0,
                'dislikes': ratings['dislikes'] or 0
            })
        except Post.DoesNotExist:
            return JsonResponse({'error': 'Пост не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)



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
