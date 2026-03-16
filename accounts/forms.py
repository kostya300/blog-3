from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Profile

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='Новый пароль', widget=forms.PasswordInput(attrs={'class': 'form-control input-field','placeholder': 'Введите новый пароль','required': True,
            'id': 'id_new_password1'}))
    new_password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control input-field',
            'placeholder': 'Повторите новый пароль',
            'required': True,
            'id': 'id_new_password2'
        })
    )
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    _('Введённые пароли не совпадают.'),
                    code='password_mismatch'
                )


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Адрес электронной почты',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email',
            'required': True,
        })
    )


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'required': True,
            'placeholder': ''
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'required': True,
            'placeholder': ''
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Remember me'
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Неверное имя пользователя или пароль."
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError("Аккаунт неактивен.")
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': ''
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': ''
        })
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': ''
        })
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': ''
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control underline-input'}),
        label='Имя пользователя'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control underline-input'}),
        label='Email'
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control underline-input', 'placeholder': '+7 (999) 123-45-67'}),
        label='Телефон'
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'О себе'}),
        required=False,
        label='Биография'
    )
    profession = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control underline-input', 'placeholder': 'Профессия'}),
        required=False,
        label='Профессия'
    )
    avatar = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control underline-input'}),
        required=False,
        label='Аватар'
    )

    class Meta:
        model = Profile
        fields = ['phone_number', 'bio', 'profession', 'avatar']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('Email должен быть уникальным')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class UserUpdateForm(forms.ModelForm):
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control underline-input', 'placeholder': '+7 (999) 123-45-67'}),
        label='Телефон'
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'О себе'}),
        required=False,
        label='Биография'
    )
    profession = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control underline-input', 'placeholder': 'Профессия'}),
        required=False,
        label='Профессия'
    )
    avatar = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control underline-input'}),
        required=False,
        label='Аватар'
    )

    class Meta:
        model = Profile
        fields = ['phone_number', 'bio', 'profession', 'avatar']