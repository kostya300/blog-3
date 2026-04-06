from django import forms
from .models import Comment, Post
from django_ckeditor_5.widgets import CKEditor5Widget  # Импортируем новый виджет


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
    query = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск'
        })
    )


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
        fields = ('name', 'body')
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

        if self.user and self.user.is_authenticated:
            self.fields['name'].initial = self.user.get_full_name() or self.user.username
            self.fields['name'].widget.attrs['readonly'] = True


    def save(self, commit=True):
        comment = super().save(commit=False)
        comment.post = self.post

        if self.user and self.user.is_authenticated:
            comment.author = self.user
            comment.name = self.user.get_full_name() or self.user.username
            comment.email = self.user.email
        else:
            comment.email = ''

        parent_id = self.cleaned_data.get("parent")
        if parent_id:
            comment.parent_id = parent_id

        if commit:
            comment.save()
        return comment



class PostCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем виджеты и классы
        self.fields["body"].required = False  # Обходная проверка, если CKEditor5 не отправляет пустые строки
        for field in self.fields:
            if field != "title" and field != "body":  # title и body обрабатываются отдельно
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off',
                })
        self.fields['tags'].widget.attrs.update({
            'data-role': 'tagsinput',
            'class': 'form-control tags-input'
        })

    class Meta:
        model = Post
        fields = (
            'title',
            'category',
            'author',
            'body',
            'status',
            'image',
            'tags'
        )
        widgets = {
            'title': CKEditor5Widget(config_name='default'),  # Для заголовка — упрощённый редактор
            'body': CKEditor5Widget(config_name='extends'),   # Для текста — расширенный
            'category': forms.Select(attrs={'class': 'form-control'}),
            'author': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PostUpdateForm(PostCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем updater и fixed
        self.fields['updater'].widget.attrs.update({'class': 'form-control'})
        self.fields['fixed'].widget.attrs.update({'class': 'form-check-input'})

    class Meta(PostCreateForm.Meta):
        fields = PostCreateForm.Meta.fields + ('updater', 'fixed')