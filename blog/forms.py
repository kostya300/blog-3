from django import forms

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
