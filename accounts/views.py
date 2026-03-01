from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages

from .forms import CustomLoginForm,SignUpForm

class LoginView(generic.FormView):
    form_class = CustomLoginForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('blog:post_list')

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        # Обработка remember_me
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)

        return super().form_valid(form)

class CustomLoginView(LoginView):
    form_class = CustomLoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # Установим время истечения сеанса равным 0 секундам. Таким образом, он автоматически закроет сеанс после закрытия браузера. И обновим данные.
            self.request.session.set_expiry(0)
            self.request.session.modified = True

        # В противном случае сеанс браузера будет таким же как время сеанса cookie "SESSION_COOKIE_AGE", определенное в settings.py
        return super(CustomLoginView, self).form_valid(form)
class SignUpView(generic.CreateView):
    form_class = SignUpForm
    initial = None
    template_name = 'registration/signup.html'
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to='blog:post_list')
        return super(SignUpView, self).dispatch(request, *args, **kwargs)
    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')

            return redirect(to='login')

        return render(request, self.template_name, {'form': form})
    def form_valid(self, form):
        response = super().form_valid(form)
        return response