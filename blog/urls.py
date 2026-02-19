from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # представления поста
    path('', views.PostListView.as_view(), name='post_list'),
    path('<int:year>/<int:month>/<int:day>/<slug:slug>/',
         views.post_detail,
         name='post_detail'),
    path('about/', views.about, name='about'),
    path('login/', views.login, name='login'),
]
