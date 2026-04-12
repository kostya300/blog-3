from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # представления поста
    path('', views.PostListView.as_view(), name='post_list'),
    path('category/<slug:category_slug>/', views.post_list_by_category, name='post_list_by_category'),
    path('search/', views.post_search, name='post_search'),
    path('<int:year>/<int:month>/<int:day>/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('about/', views.about, name='about'),
    path('<int:post_id>/comment/', views.post_comment, name='post_comment'),
    path('comment/create/<int:post_id>/', views.comment_create, name='comment_create'),
    path('tag/<slug:tag_slug>/', views.PostListView.as_view(), name='post_list_by_tag'),
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/update/', views.PostUpdateView.as_view(), name='post_update'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('subscribed/', views.subscribed_done, name='subscribed_done'),
    path('travel/', views.travel, name='travel'),
    path('switch-theme/', views.switch_theme, name='switch_theme'),
    path('like/', views.toggle_like, name='toggle_like'),
    path('comment/<int:pk>/delete/', views.user_comment_delete, name='user_comment_delete'),
    path('like-comment/', views.toggle_comment_like, name='toggle_comment_like'),

]
