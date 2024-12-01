from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, ProfileUpdateForm
from operations.models import Category
from .models import Profile

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Category.create_default_categories(user)
            Profile.create_profile(user)
            login(request, user)
            return redirect('operations:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            base64_data = request.POST.get('avatar_base64')
            if base64_data:
                profile = request.user.profile
                profile.avatar_base64 = base64_data
                profile.save()
                messages.success(request, 'Аватар успешно обновлен!')
            return redirect('operations:dashboard')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении аватара: {str(e)}')
    
    return render(request, 'accounts/update_profile.html')