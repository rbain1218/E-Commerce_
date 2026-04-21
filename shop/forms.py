from django import forms
from .models import Product, OfferBanner

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'title', 'description', 'price', 'image', 'stock']

class OfferBannerForm(forms.ModelForm):
    class Meta:
        model = OfferBanner
        fields = ['title', 'subtitle', 'button_text', 'button_link', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'button_text': forms.TextInput(attrs={'class': 'form-control'}),
            'button_link': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
