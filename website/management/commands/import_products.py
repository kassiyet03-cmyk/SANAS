import os
import sys
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.utils.text import slugify
from website.models import Category, Item, ItemImage

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Transliteration map for Cyrillic to Latin
CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
}


def transliterate(text):
    """Transliterate Cyrillic to Latin characters"""
    result = []
    for char in text:
        if char in CYRILLIC_TO_LATIN:
            result.append(CYRILLIC_TO_LATIN[char])
        else:
            result.append(char)
    return ''.join(result)


class Command(BaseCommand):
    help = 'Import products from chkz.kz website'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('Starting product import from chkz.kz...'))

        # Base URL
        base_url = 'https://chkz.kz'

        # Products data structure based on the website
        products_data = {
            'Воздушные винтовые компрессоры': [
                {
                    'name': 'ДЭН "СТАНДАРТ"',
                    'description': 'Стандартные электроприводные винтовые компрессорные установки',
                    'short_desc': 'Стандартные винтовые компрессоры для промышленного применения',
                },
                {
                    'name': 'ДЭН "ОПТИМ"',
                    'description': 'Винтовые компрессоры с частотным регулированием для оптимальной производительности',
                    'short_desc': 'Компрессоры с частотным регулированием',
                },
                {
                    'name': 'ДЭН "ВОЛЬТ"',
                    'description': 'Установки с высоковольтным двигателем для промышленных предприятий',
                    'short_desc': 'Высоковольтные компрессорные установки',
                },
                {
                    'name': 'ДЭН "ШАХТЕР"',
                    'description': 'Взрывозащищенные компрессоры для шахт и опасных производств',
                    'short_desc': 'Взрывозащищенные варианты для горнодобывающей промышленности',
                },
                {
                    'name': 'ДЭН Ш-ОР/Ш-Р',
                    'description': 'Специализированные конфигурации компрессорных установок',
                    'short_desc': 'Дополнительные конфигурации компрессоров',
                },
                {
                    'name': 'ДЭН "ЭКОНОМ"',
                    'description': 'Экономичная линейка компрессорного оборудования',
                    'short_desc': 'Экономичные компрессорные установки',
                },
                {
                    'name': 'КВ (дизельные)',
                    'description': 'Дизельные винтовые компрессорные установки для автономной работы',
                    'short_desc': 'Дизельные компрессорные установки',
                },
            ],
            'Безмасляные компрессоры': [
                {
                    'name': 'КС Серия',
                    'description': 'Спиральные безмасляные компрессорные установки для чистого сжатого воздуха',
                    'short_desc': 'Спиральные компрессорные установки',
                },
                {
                    'name': 'ДЭН-ШМБ Серия',
                    'description': 'Безмасляные винтовые компрессоры для медицины и пищевой промышленности',
                    'short_desc': 'Безмасляные винтовые варианты',
                },
            ],
            'Дополнительное оборудование': [
                {
                    'name': 'Поршневые компрессоры',
                    'description': 'Компрессоры малой производительности для гаражей и мастерских',
                    'short_desc': 'Малая производительность для гаражного применения',
                },
                {
                    'name': 'БКК (Блок-контейнерные станции)',
                    'description': 'Модульные блок-контейнерные компрессорные установки',
                    'short_desc': 'Блок-контейнерные компрессорные установки',
                },
                {
                    'name': 'Азотные станции',
                    'description': 'Установки для генерации азота из сжатого воздуха',
                    'short_desc': 'Генерация азота',
                },
                {
                    'name': 'Дизель-генераторные установки',
                    'description': 'Автономные источники электроэнергии',
                    'short_desc': 'Дизель-генераторы',
                },
                {
                    'name': 'Оборудование подготовки воздуха',
                    'description': 'Осушители, фильтры, сепараторы для очистки сжатого воздуха',
                    'short_desc': 'Осушители, фильтры, сепараторы',
                },
                {
                    'name': 'Воздухосборники',
                    'description': 'Ресиверы для хранения сжатого воздуха',
                    'short_desc': 'Ресиверы/баки для сжатого воздуха',
                },
                {
                    'name': 'Системы управления',
                    'description': 'Блоки управления компрессорными системами',
                    'short_desc': 'Системы управления компрессорами',
                },
            ],
            'Запасные части': [
                {
                    'name': 'Комплект фильтров',
                    'description': 'Впускные клапаны, клапаны минимального давления, термостатические клапаны',
                    'short_desc': 'Фильтры воздушные и масляные',
                },
                {
                    'name': 'Винтовые блоки',
                    'description': 'Винтовые блоки для компрессоров различных моделей',
                    'short_desc': 'Компактные модули',
                },
                {
                    'name': 'Охладители',
                    'description': 'Масло для компрессоров, радиаторы и системы охлаждения',
                    'short_desc': 'Компрессорное масло, радиаторы',
                },
                {
                    'name': 'Блоки управления',
                    'description': 'Соленоиды, предохранительные клапаны, ремни',
                    'short_desc': 'Электронные блоки управления',
                },
            ],
        }

        # Import products
        for category_name, products in products_data.items():
            if not dry_run:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={
                        'slug': slugify(transliterate(category_name)),
                        'description': f'Категория {category_name}'
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'[+] Created category: {category_name}'))
            else:
                self.stdout.write(f'[DRY RUN] Would create category: {category_name}')

            for idx, product in enumerate(products, 1):
                product_name = product['name']

                if not dry_run:
                    item, created = Item.objects.get_or_create(
                        title=product_name,
                        defaults={
                            'slug': slugify(transliterate(product_name)),
                            'category': category,
                            'description': product['description'],
                            'short_description': product['short_desc'],
                            'status': 'published',
                            'order': idx,
                        }
                    )

                    if created:
                        self.stdout.write(f'  [+] Created product: {product_name}')
                    else:
                        self.stdout.write(f'  [-] Product already exists: {product_name}')
                else:
                    self.stdout.write(f'[DRY RUN] Would create product: {product_name}')

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Product import completed!'))

        if not dry_run:
            total_categories = Category.objects.count()
            total_items = Item.objects.count()
            self.stdout.write(self.style.SUCCESS(f'\nTotal categories: {total_categories}'))
            self.stdout.write(self.style.SUCCESS(f'Total products: {total_items}'))
