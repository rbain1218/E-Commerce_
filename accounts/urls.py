from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify/', views.verify, name='verify'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot/', views.forgot_password, name='forgot'),
    path('reset/', views.reset_password, name='reset_password'),
    path('dashboard/', views.seller_dashboard, name='dashboard'),
]
