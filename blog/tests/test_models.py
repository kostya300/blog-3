from django.test import TestCase
from django.contrib.auth.models import User
from blog.models import Post, Comment
class PostModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='john', email='', password='')
        Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=user,
            body='Test content',
            status=Post.Status.PUBLISHED

        )
    def test_post_creation(self):
        post = Post.objects.get(slug='test-post')
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.status, Post.Status.PUBLISHED)

    def test_str_representation(self):
        post = Post.objects.get(slug='test-post')
        self.assertEqual(str(post), 'Test Post')
class CommentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=user,
            body='Test content'
        )
        Comment.objects.create(
            post=post,
            name='John Doe',
            email='john@example.com',
            body='Great post!'
        )

    def test_comment_creation(self):
        comment = Comment.objects.get(name='John Doe')
        self.assertEqual(comment.post.title, 'Test Post')
        self.assertTrue(comment.active)

    def test_comment_str_representation(self):
        comment = Comment.objects.get(name='John Doe')
        expected_str = f'Comment by John Doe on {comment.post}'
        self.assertEqual(str(comment), expected_str)