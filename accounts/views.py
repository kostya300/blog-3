from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy, NoReverseMatch
from django.views import generic
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import UpdateView
from django.db import transaction
from .forms import CustomLoginForm, SignUpForm,UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from .models import Profile
from django.conf import settings
class ProfileDetailView(generic.DetailView):
    model = Profile
    context_object_name = 'profile'
    template_name = 'registration/profile.html'

    def get_object(self, queryset=None):
        # Получаем профиль по slug из URL
        slug = self.kwargs.get('slug')
        return get_object_or_404(Profile, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Профиль пользователя: {self.object.user.username}',
        return context

class ProfileUpdateView(UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'registration/profile_edit.html'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование профиля пользователя: {self.request.user.username}'
        return context

    def form_valid(self, form):
        with transaction.atomic():
            form.save()
        messages.success(self.request, 'Профиль успешно обновлён!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'accounts:profile_detail',
            kwargs={'slug': self.request.user.profile.slug}
        )

class CustomLoginView(generic.FormView):
    form_class = CustomLoginForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('blog:post_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['RECAPTCHA_SITE_KEY'] = settings.RECAPTCHA_PUBLIC_KEY
        return context

    def get_form_kwargs(self):
        """Передаём request в форму для обработки remember_me"""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        # Обработка remember_me
        remember_me = form.cleaned_data.get('remember_me')
        if remember_me:
            # Сессия будет жить 2 недели
            self.request.session.set_expiry(1209600)  # 2 недели в секундах
        else:
            # Сессия закроется при закрытии браузера
            self.request.session.set_expiry(0)

        messages.success(self.request, 'Вы успешно вошли в систему!')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка входа. Проверьте данные.')
        return super().form_invalid(form)



class SignUpView(generic.CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Вы уже авторизованы.')
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Сохраняем пользователя
        user = form.save()

        # Автоматически авторизуем пользователя после регистрации
        login(self.request, user)

        username = form.cleaned_data.get('username')
        messages.success(
            self.request,
            f'Добро пожаловать, {username}! Ваш аккаунт успешно создан.'
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Ошибка регистрации. Проверьте введённые данные.'
        )
        return super().form_invalid(form)
class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'registration/change_password.html'
    success_message = 'Пароль изменён'

    def get_success_url(self):
        try:
            # Используем существующий URL — profile_detail
            # Для slug берём slug текущего пользователя
            return reverse_lazy(
                'accounts:profile_detail',
                kwargs={'slug': self.request.user.profile.slug}
            )
        except NoReverseMatch:
            return reverse_lazy('blog:post_list')


