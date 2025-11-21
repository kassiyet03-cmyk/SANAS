from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Category for organizing items"""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL-адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    """Main item model for products/services"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'Архив'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        verbose_name="Категория"
    )
    description = models.TextField(verbose_name="Описание")
    short_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Краткое описание"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена"
    )
    main_image = models.ImageField(
        upload_to='items/%Y/%m/',
        blank=True,
        verbose_name="Главное изображение"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    featured = models.BooleanField(default=False, verbose_name="Избранное")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Товар/Услуга"
        verbose_name_plural = "Товары/Услуги"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class ItemImage(models.Model):
    """Additional images for items"""
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Товар/Услуга"
    )
    image = models.ImageField(upload_to='items/%Y/%m/', verbose_name="Изображение")
    caption = models.CharField(max_length=200, blank=True, verbose_name="Подпись")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товара"
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"{self.item.title} - Изображение {self.order}"
