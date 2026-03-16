from django import forms
from .models import Comment, Post


class EmailPostForm(forms.Form):
    name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'name',
            'placeholder': 'Имя'
        }),
        label='Имя *'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'placeholder': 'Почта'
        }),
        label='Почта *'
    )
    to = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'to',
            'placeholder': 'Получатель'
        }),
        label='Получатель'
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'message',
            'cols': '30',
            'rows': '10',
            'placeholder': 'Сообщение'
        }),
        label='Сообщение'
    )

class SearchForm(forms.Form):
    query = forms.CharField(label='',widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск'
        }))

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'name',
                'placeholder': 'Имя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'email',
                'placeholder': 'ваш емайл'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'message',
                'rows': 10,
                'cols': 30,
                'placeholder': 'Ваш комментарий...'
            })
        }
        labels = {
            'name': 'Name',
            'email': 'Email',
            'body': 'Сообщение'
        }
class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('name','user','email','body','created','updated','active')
    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы под Bootstrap
        """
        super().__init__(*args, **kwargs)
        for field in  self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off',
            })