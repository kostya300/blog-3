from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views import generic
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
class SignUpView(generic.CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('accounts:login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        return response