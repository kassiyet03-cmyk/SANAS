from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Category, Item, ItemImage


class ItemImageInline(admin.TabularInline):
    """Inline admin for item images"""
    model = ItemImage
    extra = 1
    fields = ('image', 'caption', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    classes = ('collapse',)
    verbose_name = "Дополнительное изображение"
    verbose_name_plural = "Дополнительные изображения (необязательно)"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = "Превью"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model"""
    list_display = ('name', 'item_count', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('📁 Категория', {
            'fields': ('name', 'slug', 'description'),
            'description': 'Название категории товаров'
        }),
    )

    def item_count(self, obj):
        count = obj.items.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            count
        )
    item_count.short_description = "Количество товаров"


class ItemAdminForm(forms.ModelForm):
    """Custom form with better help text for admins"""
    class Meta:
        model = Item
        fields = '__all__'
        help_texts = {
            'title': 'Название товара, как оно будет отображаться на сайте',
            'slug': 'URL-адрес (заполняется автоматически)',
            'category': 'Выберите категорию товара',
            'short_description': 'Краткое описание для карточки товара (1-2 предложения)',
            'description': 'Полное описание товара с характеристиками',
            'main_image': 'Главное фото товара (рекомендуемый размер: 800x600)',
            'price': 'Цена в тенге (можно оставить пустым если "по запросу")',
            'status': 'Черновик - не показывается на сайте, Опубликовано - видно всем',
            'featured': 'Показывать на главной странице',
            'order': 'Порядок сортировки (меньше = выше в списке)',
        }
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 10}),
        }


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin interface for Item model"""
    form = ItemAdminForm
    list_display = (
        'title',
        'category',
        'status',
        'featured',
        'image_preview',
        'created_at'
    )
    list_filter = ('status', 'featured', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'featured')
    readonly_fields = ('created_at', 'updated_at', 'main_image_preview')
    inlines = [ItemImageInline]
    save_on_top = True  # Save buttons at top too

    fieldsets = (
        ('📦 Основная информация', {
            'fields': ('title', 'slug', 'category'),
            'description': 'Введите название и выберите категорию товара'
        }),
        ('📝 Описание товара', {
            'fields': ('short_description', 'description'),
            'description': 'Добавьте описание товара для покупателей'
        }),
        ('🖼️ Изображение', {
            'fields': ('main_image', 'main_image_preview'),
            'description': 'Загрузите фото товара'
        }),
        ('⚙️ Настройки публикации', {
            'fields': ('price', 'status', 'featured', 'order'),
            'description': 'Настройте отображение товара на сайте'
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 75px; border-radius: 3px;" />',
                obj.main_image.url
            )
        return "Нет изображения"
    image_preview.short_description = "Изображение"

    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 400px; border-radius: 5px;" />',
                obj.main_image.url
            )
        return "Нет изображения"
    main_image_preview.short_description = "Превью главного изображения"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category')


@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    """Admin interface for ItemImage model"""
    list_display = ('item', 'caption', 'order', 'image_preview', 'uploaded_at')
    list_filter = ('uploaded_at', 'item')
    search_fields = ('item__title', 'caption')
    list_editable = ('order',)
    readonly_fields = ('uploaded_at', 'large_image_preview')

    fieldsets = (
        ('Основная информация', {
            'fields': ('item', 'image', 'caption', 'order')
        }),
        ('Превью', {
            'fields': ('large_image_preview',)
        }),
        ('Дополнительная информация', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 75px; border-radius: 3px;" />',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = "Превью"

    def large_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 400px; max-width: 600px; border-radius: 5px;" />',
                obj.image.url
            )
        return "Нет изображения"
    large_image_preview.short_description = "Изображение"


# Customize admin site
admin.site.site_header = "SANAS - Управление сайтом"
admin.site.site_title = "SANAS"
admin.site.index_title = "Панель управления"

# Quick actions for admin
class QuickAddItemAdmin(admin.ModelAdmin):
    """Simplified view for quick product addition"""
    pass
