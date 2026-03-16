from django.contrib.auth.views import LoginView
from django.urls import path
from . import views

from .views import (
    CustomLoginView,
    SignUpView,
    ChangePasswordView,
    ProfileUpdateView,
    ProfileDetailView
)
from django.contrib.auth import views as auth_views

app_name = 'accounts'
urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    # path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('password_change/', ChangePasswordView.as_view(), name='password_change'),
    path('user/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('user/<slug:slug>/', ProfileDetailView.as_view(), name='profile_detail'),

]
