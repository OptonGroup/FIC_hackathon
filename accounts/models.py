from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    
    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

    @classmethod
    def create_profile(cls, user):
        """Создает профиль для пользователя"""
        profile = cls(user=user)
        profile.save()
        return profile
