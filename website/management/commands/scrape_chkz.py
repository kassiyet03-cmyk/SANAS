import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from website.models import Category, Item

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
    help = 'Import simplified product catalog from chkz.kz'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before import',
        )

    def handle(self, *args, **options):
        clear_existing = options['clear']

        if clear_existing:
            self.stdout.write(self.style.WARNING('Clearing existing products...'))
            Item.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Database cleared!'))

        self.stdout.write(self.style.SUCCESS('Importing products from chkz.kz...'))

        # Simplified category structure based on chkz.kz
        categories_data = {
            'Воздушные винтовые компрессоры': {
                'description': 'Электрические и дизельные винтовые компрессоры различной мощности',
                'products': [
                    {
                        'name': 'ДЭН "СТАНДАРТ"',
                        'description': 'Стандартные электроприводные винтовые компрессорные установки для промышленного применения. Надежное решение для производств с постоянной потребностью в сжатом воздухе.',
                        'short': 'Стандартные винтовые компрессоры'
                    },
                    {
                        'name': 'ДЭН "ОПТИМ"',
                        'description': 'Винтовые компрессоры с частотным регулированием для оптимальной производительности и энергоэффективности. Автоматически подстраиваются под потребление воздуха.',
                        'short': 'Компрессоры с частотным регулированием'
                    },
                    {
                        'name': 'ДЭН "ВОЛЬТ"',
                        'description': 'Установки с высоковольтным двигателем для крупных промышленных предприятий. Мощность от 90 до 315 кВт.',
                        'short': 'Высоковольтные компрессорные установки'
                    },
                    {
                        'name': 'ДЭН "ШАХТЕР"',
                        'description': 'Взрывозащищенные компрессоры для шахт и опасных производств. Соответствуют требованиям безопасности для работы в особых условиях.',
                        'short': 'Взрывозащищенные компрессоры'
                    },
                    {
                        'name': 'ДЭН "ЭКОНОМ"',
                        'description': 'Экономичная линейка компрессорного оборудования для малого и среднего бизнеса. Оптимальное соотношение цены и качества.',
                        'short': 'Экономичные компрессорные установки'
                    },
                    {
                        'name': 'КВ (дизельные)',
                        'description': 'Дизельные винтовые компрессорные установки для автономной работы без подключения к электросети. Идеальны для строительных площадок.',
                        'short': 'Дизельные компрессорные установки'
                    },
                ]
            },
            'Безмасляные компрессоры': {
                'description': 'Компрессоры для производства чистого сжатого воздуха без масла',
                'products': [
                    {
                        'name': 'КС Серия',
                        'description': 'Спиральные безмасляные компрессорные установки для производства чистого сжатого воздуха. Применяются в медицине, пищевой промышленности, фармацевтике.',
                        'short': 'Спиральные безмасляные компрессоры'
                    },
                    {
                        'name': 'ДЭН-ШМБ Серия',
                        'description': 'Безмасляные винтовые компрессоры для медицины и пищевой промышленности. Гарантируют 100% чистоту воздуха.',
                        'short': 'Безмасляные винтовые компрессоры'
                    },
                ]
            },
            'Поршневые компрессоры': {
                'description': 'Компрессоры малой производительности для гаражей и мастерских',
                'products': [
                    {
                        'name': 'Поршневые компрессоры малой мощности',
                        'description': 'Компактные поршневые компрессоры для гаражей, мастерских и небольших производств. Мощность от 1,5 до 5,5 кВт.',
                        'short': 'Компрессоры для гаражей и мастерских'
                    },
                ]
            },
            'Оборудование подготовки воздуха': {
                'description': 'Осушители, фильтры, сепараторы для очистки сжатого воздуха',
                'products': [
                    {
                        'name': 'Осушители воздуха',
                        'description': 'Рефрижераторные и адсорбционные осушители для удаления влаги из сжатого воздуха. Защита оборудования от коррозии.',
                        'short': 'Рефрижераторные и адсорбционные осушители'
                    },
                    {
                        'name': 'Фильтры сжатого воздуха',
                        'description': 'Циклонные сепараторы и магистральные фильтры для очистки воздуха от масла, воды и механических примесей.',
                        'short': 'Фильтры и сепараторы'
                    },
                    {
                        'name': 'Воздухосборники',
                        'description': 'Ресиверы и баки для хранения сжатого воздуха. Объем от 100 до 5000 литров.',
                        'short': 'Ресиверы для сжатого воздуха'
                    },
                ]
            },
            'Дополнительное оборудование': {
                'description': 'Азотные станции, дизель-генераторы, системы управления',
                'products': [
                    {
                        'name': 'Блок-контейнерные станции',
                        'description': 'Модульные блок-контейнерные компрессорные установки "под ключ". Полная комплектация в одном контейнере.',
                        'short': 'БКК компрессорные станции'
                    },
                    {
                        'name': 'Азотные станции',
                        'description': 'Установки для генерации азота из сжатого воздуха. Чистота азота до 99,999%.',
                        'short': 'Генераторы азота'
                    },
                    {
                        'name': 'Дизель-генераторные установки',
                        'description': 'Автономные источники электроэнергии мощностью от 10 до 500 кВА.',
                        'short': 'Дизель-генераторы'
                    },
                    {
                        'name': 'Системы управления',
                        'description': 'Блоки управления компрессорными системами. Автоматический контроль и мониторинг работы станции.',
                        'short': 'Системы управления компрессорами'
                    },
                ]
            },
        }

        total_products = 0
        total_categories = 0

        for category_name, cat_data in categories_data.items():
            self.stdout.write(f'\n[+] Category: {category_name}')

            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'slug': slugify(transliterate(category_name)),
                    'description': cat_data['description']
                }
            )

            if created:
                total_categories += 1
                self.stdout.write(self.style.SUCCESS(f'    Created category'))
            else:
                self.stdout.write(f'    Category exists')

            for idx, product in enumerate(cat_data['products'], 1):
                item, created = Item.objects.get_or_create(
                    title=product['name'],
                    defaults={
                        'slug': slugify(transliterate(product['name'])),
                        'category': category,
                        'description': product['description'],
                        'short_description': product['short'],
                        'status': 'published',
                        'order': idx,
                    }
                )

                if created:
                    total_products += 1
                    self.stdout.write(f'    [+] {product["name"]}')
                else:
                    self.stdout.write(f'    [-] {product["name"]} (exists)')

        self.stdout.write(self.style.SUCCESS(f'\n\n[SUCCESS] Import completed!'))
        self.stdout.write(self.style.SUCCESS(f'Categories created: {total_categories}'))
        self.stdout.write(self.style.SUCCESS(f'Products created: {total_products}'))
        self.stdout.write(self.style.SUCCESS(f'\nTotal in database:'))
        self.stdout.write(self.style.SUCCESS(f'  Categories: {Category.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Products: {Item.objects.count()}'))
