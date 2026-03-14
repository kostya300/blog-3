from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # представления поста
    path('', views.PostListView.as_view(), name='post_list'),
    path('category/<slug:category_slug>/', views.post_list_by_category, name='post_list_by_category'),
    path('search/',
         views.post_search,
         name='post_search'),
    path('<int:year>/<int:month>/<int:day>/<slug:slug>/',
         views.PostDetailView.as_view(),
         name='post_detail'),
    path('<int:post_id>/share/',
         views.post_share, name='post_share'),
    path('about/', views.about, name='about'),
    path('<int:post_id>/comment/',
         views.post_comment, name='post_comment'),
    path('tag/<slug:tag_slug>/',
         views.PostListView.as_view(), name='post_list_by_tag'),
    path('travel/', views.travel, name='travel'),
]
