from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from .forms import RegisterForm, VerifyOTPForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .models import EmailOTP

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered.')
            else:
                otp = EmailOTP.generate_otp()
                EmailOTP.objects.create(email=email, otp=otp, purpose='register')
                send_mail('E-Point Registration OTP', f'Your OTP is: {otp}', None, [email])
                request.session['pending_user'] = {'username': username, 'email': email, 'password': password}
                messages.success(request, 'OTP sent to your email.')
                return redirect('accounts:verify')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify(request):
    pending = request.session.get('pending_user')
    if not pending:
        messages.error(request, 'No registration in progress.')
        return redirect('accounts:register')
    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = form.cleaned_data['otp']
            match = EmailOTP.objects.filter(email=email, otp=otp, purpose='register').last()
            if match:
                user = User.objects.create_user(
                    username=pending['username'], email=pending['email'], password=pending['password']
                )
                del request.session['pending_user']
                messages.success(request, 'Email verified. You can login now.')
                return redirect('accounts:login')
            messages.error(request, 'Invalid OTP.')
    else:
        form = VerifyOTPForm(initial={'email': pending['email']})
    return render(request, 'accounts/verify.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request, username=form.cleaned_data['username'], password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                messages.success(request, 'Logged in.')
                return redirect('shop:home')
            messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out.')
    return redirect('shop:home')

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if not User.objects.filter(email=email).exists():
                messages.error(request, 'No user with that email.')
            else:
                otp = EmailOTP.generate_otp()
                EmailOTP.objects.create(email=email, otp=otp, purpose='reset')
                send_mail('E-Point Password Reset OTP', f'Your OTP is: {otp}', None, [email])
                messages.success(request, 'Reset OTP sent. Enter OTP to set new password.')
                return redirect('accounts:reset_password')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot.html', {'form': form})

def reset_password(request):
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = form.cleaned_data['otp']
            new_password = form.cleaned_data['new_password']
            match = EmailOTP.objects.filter(email=email, otp=otp, purpose='reset').last()
            if match:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password reset. Login now.')
                return redirect('accounts:login')
            messages.error(request, 'Invalid OTP.')
    else:
        form = ResetPasswordForm()
    return render(request, 'accounts/reset.html', {'form': form})

from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

from shop.models import Product, Category
from orders.models import OrderItem, Order

@login_required
def seller_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Access restricted to sellers/admins.")
        return redirect('shop:home')
        
    from shop.forms import OfferBannerForm
    from shop.models import OfferBanner
    
    if request.method == 'POST':
        if 'update_order' in request.POST:
            order_id = request.POST.get('order_id')
            new_status = request.POST.get('status')
            order_obj = Order.objects.filter(id=order_id).first()
            if order_obj and order_obj.items.filter(product__seller=request.user).exists():
                order_obj.status = new_status
                order_obj.save()
                messages.success(request, f"Order #{order_id} status updated to {new_status}.")
            return redirect('accounts:dashboard')
            
        if 'add_banner' in request.POST:
            active_banner = OfferBanner.objects.filter(is_active=True).first()
            banner_form = OfferBannerForm(request.POST, instance=active_banner)
            if banner_form.is_valid():
                banner_form.save()
                messages.success(request, "Offer Banner updated successfully!")
            return redirect('accounts:dashboard')
            
    active_banner = OfferBanner.objects.filter(is_active=True).first()
    banner_form = OfferBannerForm(instance=active_banner) if active_banner else OfferBannerForm()
    
    recent_orders = Order.objects.filter(items__product__seller=request.user).distinct().order_by('-created_at')[:10]
        
    # Revenue calculations
    seller_items = OrderItem.objects.filter(product__seller=request.user)
    total_revenue = seller_items.aggregate(total=Sum('price'))['total'] or 0
    total_orders = Order.objects.filter(items__product__seller=request.user).distinct().count()
    total_products = Product.objects.filter(seller=request.user).count()
    
    # Calculate revenue and sales per category for pie chart
    category_data = Category.objects.filter(
        products__seller=request.user
    ).annotate(
        sales_count=Count('products__orderitem'),
        revenue=Sum('products__price')
    ).values('name', 'sales_count', 'revenue')
    
    labels = [c['name'] for c in category_data if c['sales_count'] > 0]
    data_counts = [c['sales_count'] for c in category_data if c['sales_count'] > 0]
    
    # 30-Day Sales Trend
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_sales = OrderItem.objects.filter(
        product__seller=request.user,
        order__created_at__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('order__created_at')
    ).values('date').annotate(
        daily_revenue=Sum('price')
    ).order_by('date')
    
    date_list = [(thirty_days_ago + timedelta(days=x)).date() for x in range(31)]
    revenue_dict = {d.strftime('%b %d'): 0.0 for d in date_list}
    
    for entry in daily_sales:
        dt = entry['date']
        if dt:
            dt_str = dt.strftime('%b %d')
            if dt_str in revenue_dict:
                revenue_dict[dt_str] += float(entry['daily_revenue'] or 0)
        
    trend_labels = list(revenue_dict.keys())
    trend_data = list(revenue_dict.values())
    
    # AI Predictive Analytics (Linear Regression for next 7 days)
    ai_predicted_data = []
    ai_predicted_labels = []
    
    if sum(trend_data) > 0 or len(daily_sales) > 0:
        try:
            X = np.array(range(len(trend_data))).reshape(-1, 1)
            y = np.array(trend_data)
            model = LinearRegression()
            model.fit(X, y)
            
            future_X = np.array(range(len(trend_data), len(trend_data) + 7)).reshape(-1, 1)
            predictions = model.predict(future_X)
            predictions = [max(0, round(p, 2)) for p in predictions]
            
            ai_predicted_data = predictions
            last_date = date_list[-1]
            ai_predicted_labels = [(last_date + timedelta(days=x+1)).strftime('%b %d') for x in range(7)]
        except Exception as e:
            print("Error in AI Prediction:", e)

    # Top 5 Best Selling Products
    top_products_qs = OrderItem.objects.filter(product__seller=request.user).values('product__title').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    top_products_labels = [item['product__title'][:20] + '...' if len(item['product__title']) > 20 else item['product__title'] for item in top_products_qs]
    top_products_data = [item['total_quantity'] for item in top_products_qs]
    
    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'chart_labels': labels,
        'chart_data': data_counts,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'ai_predicted_labels': ai_predicted_labels,
        'ai_predicted_data': ai_predicted_data,
        'top_products_labels': top_products_labels,
        'top_products_data': top_products_data,
        'recent_orders': recent_orders,
        'banner_form': banner_form,
    }
    return render(request, 'accounts/seller_dashboard.html', context)
