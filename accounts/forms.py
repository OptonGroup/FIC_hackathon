from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    error_messages = {
        'password_mismatch': 'Введенные пароли не совпадают.',
        'password_too_short': 'Пароль слишком короткий. Он должен содержать как минимум 8 символов.',
        'password_too_similar': 'Пароль слишком похож на имя пользователя.',
        'password_too_common': 'Пароль слишком простой.',
        'password_entirely_numeric': 'Пароль не может состоять только из цифр.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].error_messages = {
            'unique': 'Пользователь с таким именем уже существует.',
            'invalid': 'Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_',
            'required': 'Это поле обязательно для заполнения.',
        }
        self.fields['password1'].error_messages = {
            'required': 'Это поле обязательно для заполнения.',
        }
        self.fields['password2'].error_messages = {
            'required': 'Это поле обязательно для заполнения.',
        }

        # Русские названия полей
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'})
        }