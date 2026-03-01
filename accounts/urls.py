from django.contrib.auth.views import LoginView
from django.urls import path
from . import views
from .views import SignUpView
from django.contrib.auth import views as auth_views
app_name = 'accounts'
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
]
