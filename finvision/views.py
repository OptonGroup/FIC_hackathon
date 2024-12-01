from django.shortcuts import render
from operations.views import get_currency_rates

def main_page(request):
    # Получаем курсы валют
    currency_rates = get_currency_rates()
    
    context = {
        'currency_rates': currency_rates
    }
    
    return render(request, 'main.html', context) 