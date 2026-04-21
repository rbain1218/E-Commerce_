from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, OfferBanner, Category
from .forms import ProductForm
from orders.cart import Cart
import random

def home(request):
    default_categories = [
        {'name': 'Mobiles', 'slug': 'mobiles'},
        {'name': 'Fashion', 'slug': 'fashion'},
        {'name': 'Electronics', 'slug': 'electronics'},
        {'name': 'Home', 'slug': 'home'},
        {'name': 'Sports', 'slug': 'sports'},
    ]

    categories = list(Category.objects.all())
    if not categories:
        for item in default_categories:
            Category.objects.get_or_create(name=item['name'], slug=item['slug'])
        categories = list(Category.objects.all())

    products = Product.objects.order_by('-created_at')
    active_offer = OfferBanner.objects.filter(is_active=True).first()
    return render(request, 'shop/home.html', {'products': products, 'offer': active_offer, 'categories': categories})

from .recommendations import get_similar_products

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.order_by('-created_at')
    return render(request, 'shop/category_detail.html', {'category': category, 'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Use AI Recommendation Engine
    ai_recommended_products = get_similar_products(product.id, num_recommendations=4)
    
    # Fallback to category if AI model fails or lacks data
    if not ai_recommended_products:
        ai_recommended_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4] if product.category else []
        
    return render(request, 'shop/product_detail.html', {'product': product, 'related_products': ai_recommended_products})

@login_required
def sell_product(request):
    if not request.user.is_superuser:
        messages.error(request, "Only admins can sell products.")
        return redirect('shop:home')
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            prod = form.save(commit=False)
            prod.seller = request.user
            prod.save()
            messages.success(request, 'Product listed.')
            return redirect('shop:home')
    else:
        form = ProductForm()
    return render(request, 'shop/sell.html', {'form': form})



@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = Cart(request)
    cart.add(product_id=product.id, price=float(product.price), title=product.title)
    messages.success(request, 'Added to cart.')
    return redirect('shop:product_detail', pk=pk)


def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/products.html', {'products': products})

def info_page(request, slug):
    titles = {
        'about-us': 'About Us',
        'careers': 'Careers',
        'press': 'Press',
        'payments': 'Payments',
        'shipping': 'Shipping',
        'cancellation': 'Cancellation & Returns',
        'faq': 'FAQ',
        'return-policy': 'Return Policy',
        'terms': 'Terms of Use',
        'security': 'Security',
        'privacy': 'Privacy',
    }
    title = titles.get(slug, 'Information')
    return render(request, 'shop/info.html', {'title': title, 'slug': slug})


def home(request):
    default_categories = [
        {'name': 'Mobiles', 'slug': 'mobiles'},
        {'name': 'Fashion', 'slug': 'fashion'},
        {'name': 'Electronics', 'slug': 'electronics'},
        {'name': 'Home', 'slug': 'home'},
        {'name': 'Sports', 'slug': 'sports'},
    ]

    categories = list(Category.objects.all())
    if not categories:
        for item in default_categories:
            Category.objects.get_or_create(name=item['name'], slug=item['slug'])
        categories = list(Category.objects.all())

    products = list(Product.objects.order_by('-created_at'))

    
    for p in products:
        p.discount = random.randint(10, 65)
        p.old_price = int(p.price + (p.price * p.discount / 100))

    active_offer = OfferBanner.objects.filter(is_active=True).first()

    return render(request, 'shop/home.html', {
        'products': products,
        'offer': active_offer,
        'categories': categories
    })