from django.db import models
from django.contrib.auth.models import User
import base64

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar_base64 = models.TextField(default='', blank=True)  # Храним изображение в base64
    
    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

    @classmethod
    def create_profile(cls, user):
        """Создает профиль для пользователя"""
        # Читаем дефолтное изображение и конвертируем в base64
        try:
            with open('static/img/default-avatar.png', 'rb') as img_file:
                default_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        except:
            default_base64 = ''  # Если файл не найден, оставляем пустым
            
        profile = cls(user=user, avatar_base64=default_base64)
        profile.save()
        return profile
