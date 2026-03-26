from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count

from blog.models import Post, Category

from blog.views import PostListView


class PostListViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Создаём категорию
        self.category = Category.objects.create(
            title='Test Category',
            slug='test-category',
        )
        # Создаём тег
        self.tag = Tag.objects.create(name='Test Tag', slug='test-tag')
        # Создаём опубликованные посты
        self.post1 = Post.objects.create(
            title='Post 1',
            slug='post-1',
            author_id=1,
            status=Post.Status.PUBLISHED,
            category=self.category,
            views=10
        )
        self.post2 = Post.objects.create(
            title='Post 2',
            slug='post-2',
            author_id=1,
            status=Post.Status.PUBLISHED,
            category=self.category,
            views=20
        )
        self.post3 = Post.objects.create(
            title='Post 3',
            slug='post-3',
            author_id=1,
            status=Post.Status.PUBLISHED,
            category=self.category,
            views=5
        )
        # Добавляем тег к посту
        self.post1.tags.add(self.tag)

    def test_get_queryset_without_tag(self):
        """Тест get_queryset без тега — должны вернуться все опубликованные посты"""
        view = PostListView()
        view.kwargs = {}
        view.request = self.factory.get('/')

        queryset = view.get_queryset()

        self.assertEqual(queryset.count(), 3)
        self.assertIn(self.post1, queryset)
        self.assertIn(self.post2, queryset)
        self.assertIn(self.post3, queryset)
        self.assertIsNone(view.tag)

    def test_get_queryset_with_existing_tag(self):
        """Тест get_queryset с существующим тегом — должны вернуться посты с этим тегом"""
        view = PostListView()
        view.kwargs = {'tag_slug': 'test-tag'}
        view.request = self.factory.get('/tag/test-tag/')

        queryset = view.get_queryset()

        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.post1, queryset)
        self.assertEqual(view.tag, self.tag)

    def test_get_queryset_with_nonexistent_tag(self):
        """Тест get_queryset с несуществующим тегом — должен вернуться 404"""
        view = PostListView()
        view.kwargs = {'tag_slug': 'nonexistent-tag'}
        view.request = self.factory.get('/tag/nonexistent-tag/')

        with self.assertRaises(Exception) as context:
            view.get_queryset()
        # Уточняем проверку: get_object_or_404 вызывает Http404
        from django.http import Http404
        self.assertIsInstance(context.exception, Http404)

    def test_get_context_data_basic(self):
        """Тест get_context_data — проверка основных контекстных переменных"""
        view = PostListView()
        view.kwargs = {}
        view.request = self.factory.get('/')
        view.object_list = Post.published.all()
        view.tag = None

        context = view.get_context_data()

        # Проверяем основные переменные контекста
        self.assertIn('posts', context)
        self.assertIn('tag', context)
        self.assertIn('popular_posts', context)
        self.assertIn('most_viewed_posts', context)
        self.assertIn('categories', context)

        # Проверяем значения
        self.assertIsNone(context['tag'])
        self.assertEqual(list(context['categories']), [self.category])

    def test_get_context_data_popular_posts(self):
        """Тест popular_posts — посты с наибольшим числом комментариев"""
        # Создаём комментарии для поста 1
        Comment.objects.create(post=self.post1, name='User1', body='Comment 1')
        Comment.objects.create(post=self.post1, name='User2', body='Comment 2')
        # Создаём комментарий для поста 2
        Comment.objects.create(post=self.post2, name='User3', body='Comment 3')

        view = PostListView()
        view.kwargs = {}
        view.request = self.factory.get('/')
        view.object_list = Post.published.all()
        view.tag = None

        context = view.get_context_data()
        popular_posts = context['popular_posts']

        # Пост 1 должен быть первым (2 комментария), пост 2 — вторым (1 комментарий)
        self.assertEqual(popular_posts[0], self.post1)
        self.assertEqual(popular_posts[1], self.post2)

    def test_get_context_data_most_viewed_posts(self):
        """Тест most_viewed_posts — посты с наибольшим числом просмотров"""
        view = PostListView()
        view.kwargs = {}
        view.request = self.factory.get('/')
        view.object_list = Post.published.all()
        view.tag = None

        context = view.get_context_data()
        most_viewed = context['most_viewed_posts']

        # Должны быть отсортированы по убыванию просмотров: пост2 (20), пост1 (10), пост3 (5)
        self.assertEqual(most_viewed[0], self.post2)
        self.assertEqual(most_viewed[1], self.post1)
        self.assertEqual(most_viewed[2], self.post3)

    def test_view_renders_correct_template(self):
        """Тест: представление использует правильный шаблон"""
        response = self.client.get(reverse('blog:post_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')

    def test_pagination(self):
        """Тест пагинации — на странице должно быть не более 3 постов"""
        # Создаём дополнительные посты для проверки пагинации
        for i in range(4):
            Post.objects.create(
                title=f'Additional Post {i}',
                slug=f'additional-post-{i}',
                author_id=1,
                status=Post.Status.PUBLISHED,
                category=self.category
            )

        response = self.client.get(reverse('blog:post_list'))

        self.assertEqual(len(response.context['posts']), 3)  # 3 поста на странице
        self.assertTrue(response.context['is_paginated'])  # Пагинация активна

    def test_tag_filter_in_url(self):
        """Тест фильтрации по тегу через URL"""
        response = self.client.get(
            reverse('blog:post_list_by_tag', kwargs={'tag_slug': 'test-tag'})
        )

        self.assertEqual(response.status_code, 200)
        posts = response.context['posts']
        self.assertEqual(posts.count(), 1)
        self.assertEqual(posts[0], self.post1)
        self.assertEqual(response.context['tag'], self.tag)
