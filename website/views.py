from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Category, Item


def index(request):
    """Render the home page"""
    # Get all categories with their published items
    categories = Category.objects.prefetch_related(
        'items'
    ).all()

    # Get all published items ordered by category and order
    items = Item.objects.filter(
        status='published'
    ).select_related('category').order_by('category__name', 'order')

    context = {
        'categories': categories,
        'items': items,
    }

    return render(request, 'index.html', context)


def product_detail(request, slug):
    """Render product detail page"""
    item = get_object_or_404(Item, slug=slug, status='published')

    # Get related items from the same category
    related_items = Item.objects.filter(
        category=item.category,
        status='published'
    ).exclude(id=item.id).order_by('order')[:3]

    context = {
        'item': item,
        'related_items': related_items,
    }

    return render(request, 'product_detail.html', context)


def contact(request):
    """Handle contact form submission"""
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Here you can add email sending or database saving logic
        # For now, we'll just add a success message

        # Example email sending (uncomment and configure if needed):
        # try:
        #     send_mail(
        #         f'Новая заявка от {name}',
        #         f'Имя: {name}\nТелефон: {phone}\nEmail: {email}\nСообщение: {message}',
        #         settings.DEFAULT_FROM_EMAIL,
        #         ['info@sanas.kz'],
        #         fail_silently=False,
        #     )
        # except Exception as e:
        #     messages.error(request, 'Произошла ошибка при отправке сообщения.')
        #     return redirect('index')

        messages.success(request, 'Спасибо за вашу заявку! Мы свяжемся с вами в ближайшее время.')
        return redirect('index')

    return redirect('index')
