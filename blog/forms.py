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
    query = forms.CharField(label='', widget=forms.TextInput(attrs={
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

class CommentCreateForm(forms.ModelForm):
    parent = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Comment
        fields = ('name', 'body')  # ❌ убрали 'email'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ваш комментарий...'
            })
        }

    def __init__(self, *args, **kwargs):
        self.post = kwargs.pop('post', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Если пользователь авторизован — подставляем имя
        if self.user and self.user.is_authenticated:
            self.fields['name'].initial = self.user.get_full_name() or self.user.username
            self.fields['name'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        comment = super().save(commit=False)
        comment.post = self.post

        # Подставляем email только если есть user, иначе оставляем пустым
        if self.user and self.user.is_authenticated:
            comment.user = self.user
            comment.name = self.user.get_full_name() or self.user.username
            comment.email = self.user.email
        else:
            comment.email = ''  # или None

        parent_id = self.cleaned_data.get("parent")
        if parent_id:
            comment.parent_id = parent_id

        if commit:
            comment.save()
        return comment
class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title',
                  'category',
                  'author',
                  'body',
                  'status',
                  'image',
                  'tags')

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы под Bootstrap
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off',
            })
            # Для тегов — особый класс, если используется Taggit
            self.fields['tags'].widget.attrs.update({
                'data-role': 'tagsinput',
                'class': 'form-control tags-input'
            })
class PostUpdateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = PostCreateForm.Meta.fields + ('updater', 'fixed')
    def __init__ (self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
        self.fields['tags'].widget.attrs.update({
            'data-role': 'tagsinput',
            "class":'form-control tags-input',
        })