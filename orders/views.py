from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .models import Order, OrderItem
from .cart import Cart
from shop.models import Product

@login_required
def cart_view(request):
    cart = Cart(request)
    return render(request, 'orders/cart.html', {'cart': list(cart), 'total': cart.total()})

@login_required
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    messages.info(request, 'Item removed.')
    return redirect('orders:cart')

@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.clear()
    cart.add(product_id=product.id, price=float(product.price), title=product.title, quantity=1)
    return redirect('orders:checkout')

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout(request):
    cart = Cart(request)
    if request.method == 'POST':
        total = Decimal(cart.total())
        
        # Create Order as pending
        order = Order.objects.create(user=request.user, total_amount=total, status='pending')
        for item in cart:
            prod = Product.objects.get(id=item['id'])
            OrderItem.objects.create(order=order, product=prod, quantity=item['quantity'], price=item['price'])
        
        # Stripe Checkout Session
        # Building line items from cart
        line_items = []
        for item in cart:
            line_items.append({
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': item['title'],
                    },
                    'unit_amount': int(float(item['price']) * 100), # Stripe requires amount in cents/paise
                },
                'quantity': item['quantity'],
            })
            
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri('/')[:-1] + '/orders/stripe-success/' + str(order.id) + '/',
                cancel_url=request.build_absolute_uri('/')[:-1] + '/orders/stripe-cancel/' + str(order.id) + '/',
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            messages.error(request, str(e))
            return redirect('orders:cart')

    return render(request, 'orders/checkout.html', {'cart': list(cart), 'total': cart.total()})

@login_required
def stripe_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'pending':
        order.status = 'success'
        order.save()
        # Decrement stock
        for item in order.items.all():
            prod = item.product
            if prod.stock >= item.quantity:
                prod.stock -= item.quantity
                prod.save()
        # Clear cart
        cart = Cart(request)
        cart.clear()
        messages.success(request, 'Payment successful! Your order stands confirmed.')
    return redirect('orders:order_list')

@login_required
def stripe_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()
        messages.error(request, 'Payment cancelled.')
    return redirect('orders:cart')

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/orders.html', {'orders': orders})

import io
from django.http import FileResponse, HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

@login_required
def generate_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Create an in-memory byte buffer
    buffer = io.BytesIO()
    
    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Draw things on the PDF
    p.setFont("Helvetica-Bold", 20)
    p.drawString(1 * inch, height - 1 * inch, "E-Point Original Invoice")
    
    p.setFont("Helvetica", 12)
    p.drawString(1 * inch, height - 1.5 * inch, f"Order ID: #{order.id}")
    p.drawString(1 * inch, height - 1.8 * inch, f"Date: {order.created_at.strftime('%B %d, %Y')}")
    p.drawString(1 * inch, height - 2.1 * inch, f"Customer: {order.user.username}")
    p.drawString(1 * inch, height - 2.4 * inch, f"Email: {order.user.email}")
    
    # Draw table header
    p.setFont("Helvetica-Bold", 12)
    y_position = height - 3 * inch
    p.drawString(1 * inch, y_position, "Item")
    p.drawString(4 * inch, y_position, "Quantity")
    p.drawString(6 * inch, y_position, "Price")
    
    # Draw line
    p.line(1 * inch, y_position - 0.1 * inch, 7.5 * inch, y_position - 0.1 * inch)
    
    # Draw items
    p.setFont("Helvetica", 12)
    y_position -= 0.5 * inch
    
    for item in order.items.all():
        p.drawString(1 * inch, y_position, str(item.product.title)[:35] + "...")
        p.drawString(4 * inch, y_position, str(item.quantity))
        p.drawString(6 * inch, y_position, f"Rs. {item.price}")
        y_position -= 0.3 * inch
    
    p.line(1 * inch, y_position, 7.5 * inch, y_position)
    y_position -= 0.3 * inch
    p.setFont("Helvetica-Bold", 14)
    p.drawString(4 * inch, y_position, "Total Amount:")
    p.drawString(6 * inch, y_position, f"Rs. {order.total_amount}")
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(1 * inch, 1 * inch, "Thank you for shopping securely with E-Point AI Marketplace.")
    
    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    
    # FileResponse sets the Content-Disposition header so that browsers present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'E-Point_Invoice_#{order.id}.pdf')
