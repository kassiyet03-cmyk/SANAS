from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.utils.text import slugify
from .models import Category, Item, ItemImage
import re


def transliterate(text):
    """Convert Cyrillic to Latin for URL slugs"""
    cyrillic = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    latin = ['a','b','v','g','d','e','yo','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','h','ts','ch','sh','sch','','y','','e','yu','ya']

    text = text.lower()
    result = ''
    for char in text:
        if char in cyrillic:
            result += latin[cyrillic.index(char)]
        elif char.isalnum():
            result += char
        else:
            result += '-'

    result = re.sub(r'-+', '-', result).strip('-')
    return result


def is_staff(user):
    return user.is_staff


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


# ============== ADMIN PANEL VIEWS ==============

def panel_login(request):
    """Login page for admin panel"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('panel_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('panel_dashboard')
        else:
            messages.error(request, 'Неверный логин или пароль')

    return render(request, 'panel/login.html')


def panel_logout(request):
    """Logout from admin panel"""
    logout(request)
    return redirect('panel_login')


def panel_dashboard(request):
    """Main dashboard for admin panel"""
    items_count = Item.objects.count()
    categories_count = Category.objects.count()
    published_count = Item.objects.filter(status='published').count()

    recent_items = Item.objects.order_by('-created_at')[:5]

    context = {
        'items_count': items_count,
        'categories_count': categories_count,
        'published_count': published_count,
        'recent_items': recent_items,
    }
    return render(request, 'panel/dashboard.html', context)


def panel_items(request):
    """List all items"""
    items = Item.objects.select_related('category').order_by('-created_at')

    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(category_id=category_id)

    # Search
    search = request.GET.get('search')
    if search:
        items = items.filter(title__icontains=search)

    paginator = Paginator(items, 10)
    page = request.GET.get('page')
    items = paginator.get_page(page)

    categories = Category.objects.all()

    context = {
        'items': items,
        'categories': categories,
    }
    return render(request, 'panel/items.html', context)


def panel_item_add(request):
    """Add new item"""
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        short_description = request.POST.get('short_description', '')
        description = request.POST.get('description', '')
        price = request.POST.get('price') or None
        status = request.POST.get('status', 'draft')
        featured = request.POST.get('featured') == 'on'

        # Generate slug
        slug = transliterate(title)

        # Check slug uniqueness
        base_slug = slug
        counter = 1
        while Item.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        item = Item.objects.create(
            title=title,
            slug=slug,
            category_id=category_id,
            short_description=short_description,
            description=description,
            price=price,
            status=status,
            featured=featured,
        )

        # Handle image upload
        if 'main_image' in request.FILES:
            item.main_image = request.FILES['main_image']
            item.save()

        messages.success(request, f'Товар "{title}" успешно добавлен!')
        return redirect('panel_items')

    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'panel/item_form.html', context)


def panel_item_edit(request, item_id):
    """Edit existing item"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == 'POST':
        item.title = request.POST.get('title')
        item.category_id = request.POST.get('category')
        item.short_description = request.POST.get('short_description', '')
        item.description = request.POST.get('description', '')
        item.price = request.POST.get('price') or None
        item.status = request.POST.get('status', 'draft')
        item.featured = request.POST.get('featured') == 'on'

        # Handle image upload
        if 'main_image' in request.FILES:
            item.main_image = request.FILES['main_image']

        item.save()
        messages.success(request, f'Товар "{item.title}" обновлен!')
        return redirect('panel_items')

    categories = Category.objects.all()
    context = {
        'item': item,
        'categories': categories,
    }
    return render(request, 'panel/item_form.html', context)


def panel_item_delete(request, item_id):
    """Delete item"""
    item = get_object_or_404(Item, id=item_id)
    title = item.title
    item.delete()
    messages.success(request, f'Товар "{title}" удален!')
    return redirect('panel_items')


def panel_categories(request):
    """List and manage categories"""
    categories = Category.objects.annotate_item_count()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name')
            slug = transliterate(name)
            description = request.POST.get('description', '')
            category = Category.objects.create(name=name, slug=slug, description=description)
            if 'image' in request.FILES:
                category.image = request.FILES['image']
                category.save()
            messages.success(request, f'Категория "{name}" добавлена!')

        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            cat = get_object_or_404(Category, id=cat_id)
            cat_name = cat.name
            cat.delete()
            messages.success(request, f'Категория "{cat_name}" удалена!')

        return redirect('panel_categories')

    context = {'categories': categories}
    return render(request, 'panel/categories.html', context)
