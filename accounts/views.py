from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomLoginForm, SignUpForm,UpdateUserForm,UpdateProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлён')
            return redirect('accounts:users-profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(
        request,
        'registration/profile.html',
        {'user_form': user_form, 'profile_form': profile_form}
    )
class CustomLoginView(generic.FormView):
    form_class = CustomLoginForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('blog:post_list')

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
            # Устанавливаем длительное время жизни сессии (2 недели)
            self.request.session.set_expiry(1209600)  # 2 недели в секундах
        else:
            # Сессия закрывается при закрытии браузера
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
class ChangePasswordView(SuccessMessageMixin,PasswordChangeView):
    template_name = 'registration/change_password.html'
    success_message = 'Successfully Changed Your Password'
    success_url = reverse_lazy('accounts:users-profile')

