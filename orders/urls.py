from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('buy/<int:product_id>/', views.buy_now, name='buy_now'),
    path('checkout/', views.checkout, name='checkout'),
    path('list/', views.order_list, name='order_list'),
    path('invoice/<int:order_id>/', views.generate_invoice, name='generate_invoice'),
    path('stripe-success/<int:order_id>/', views.stripe_success, name='stripe_success'),
    path('stripe-cancel/<int:order_id>/', views.stripe_cancel, name='stripe_cancel'),
]
