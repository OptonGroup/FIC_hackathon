from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/<int:transaction_id>/edit/', views.edit_transaction, name='edit_transaction'),
    path('transactions/<int:transaction_id>/delete/', views.delete_transaction, name='delete_transaction'),
    path('export_transactions/<str:file_format>/', views.export_transactions, name='export_transactions'),
    path('targets/', views.targets, name='targets'),
    path('targets/add/', views.add_target, name='add_target'),
    path('targets/<int:target_id>/edit/', views.edit_target, name='edit_target'),
    path('targets/<int:target_id>/delete/', views.delete_target, name='delete_target'),
    path('credits/', views.credits, name='credits'),
    path('credits/add/', views.add_credit, name='add_credit'),
    path('credits/<int:credit_id>/edit/', views.edit_credit, name='edit_credit'),
    path('credits/<int:credit_id>/delete/', views.delete_credit, name='delete_credit'),
    path('regular-payments/', views.regular_payments, name='regular_payments'),
    path('regular-payments/add/', views.add_regular_payment, name='add_regular_payment'),
    path('regular-payments/<int:payment_id>/edit/', views.edit_regular_payment, name='edit_regular_payment'),
    path('regular-payments/<int:payment_id>/delete/', views.delete_regular_payment, name='delete_regular_payment'),
    path('analytics/', views.analytics, name='analytics'),
    path('cards/', views.cards, name='cards'),
    path('cards/add/', views.add_card, name='add_card'),
    path('cards/<int:card_id>/edit/', views.edit_card, name='edit_card'),
    path('cards/<int:card_id>/delete/', views.delete_card, name='delete_card'),
    path('calendar/', views.calendar, name='calendar'),
    path('api/currency-rates/', views.get_currency_rates_api, name='currency_rates_api'),
]