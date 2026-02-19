from django.urls import path
from .views import post_list,post_detail
app_name = "blog"
urlpatterns = [
    path('', post_list, name='home'),
    path('<int:id>/about/',post_detail , name='about'),
]