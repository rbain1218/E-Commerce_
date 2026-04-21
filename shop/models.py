from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, null=True, blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class OfferBanner(models.Model):
    title = models.CharField(max_length=200, default="Big Savings on Top Brands")
    subtitle = models.TextField(default="Get the best deals on electronics, fashion, and more. Free shipping on orders over ₹500.")
    button_text = models.CharField(max_length=50, default="Shop Now")
    button_link = models.CharField(max_length=255, default="#products")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
        
    def save(self, *args, **kwargs):
        if self.is_active:
            OfferBanner.objects.filter(is_active=True).update(is_active=False)
        super(OfferBanner, self).save(*args, **kwargs)
