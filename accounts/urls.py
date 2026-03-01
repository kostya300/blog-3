from django.contrib.auth.views import LoginView
from django.urls import path
from . import views
from .views import SignUpView

app_name = 'accounts'
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
]
