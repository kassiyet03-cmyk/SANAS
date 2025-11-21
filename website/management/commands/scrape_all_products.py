import os
import sys
import time
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
    help = 'Scrape products from ts2006.kz and chkz.kz'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of products to scrape per site',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        self.stdout.write(self.style.SUCCESS('Starting product scraping...'))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        products_scraped = 0

        # Scrape from chkz.kz
        self.stdout.write(self.style.SUCCESS('\n[1] Scraping chkz.kz...'))
        try:
            products_scraped += self.scrape_chkz(headers, dry_run, limit)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error scraping chkz.kz: {str(e)}'))

        # Scrape from ts2006.kz
        self.stdout.write(self.style.SUCCESS('\n[2] Scraping ts2006.kz...'))
        try:
            products_scraped += self.scrape_ts2006(headers, dry_run, limit)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error scraping ts2006.kz: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'\n[SUCCESS] Scraping completed! Total products: {products_scraped}'))

        if not dry_run:
            total_categories = Category.objects.count()
            total_items = Item.objects.count()
            self.stdout.write(self.style.SUCCESS(f'\nDatabase stats:'))
            self.stdout.write(self.style.SUCCESS(f'  Total categories: {total_categories}'))
            self.stdout.write(self.style.SUCCESS(f'  Total products: {total_items}'))

    def scrape_chkz(self, headers, dry_run, limit):
        """Scrape products from chkz.kz"""
        base_url = 'https://chkz.kz'
        catalog_url = f'{base_url}/catalog/'

        products_count = 0

        try:
            response = requests.get(catalog_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all category sections
            categories = soup.find_all('div', class_='catalog-section') or soup.find_all('section', class_='products')

            if not categories:
                # Try alternative structure
                categories = soup.find_all('div', class_='product-category')

            for cat_section in categories[:10]:  # Limit categories
                try:
                    # Extract category name
                    cat_name_elem = cat_section.find(['h2', 'h3', 'h4'])
                    if not cat_name_elem:
                        continue

                    category_name = cat_name_elem.get_text(strip=True)

                    if not category_name:
                        continue

                    self.stdout.write(f'  Category: {category_name}')

                    if not dry_run:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={
                                'slug': slugify(transliterate(category_name)),
                                'description': f'Категория {category_name}'
                            }
                        )

                    # Find products in this category
                    product_items = cat_section.find_all(['div', 'a'], class_=['product-item', 'product-card', 'catalog-item'])[:limit]

                    for idx, product_elem in enumerate(product_items, 1):
                        try:
                            # Extract product name
                            name_elem = product_elem.find(['h3', 'h4', 'h5', 'span', 'a'], class_=['product-title', 'product-name', 'title'])
                            if not name_elem:
                                name_elem = product_elem.find(['h3', 'h4', 'h5'])

                            if not name_elem:
                                continue

                            product_name = name_elem.get_text(strip=True)

                            if not product_name or len(product_name) < 3:
                                continue

                            # Extract description
                            desc_elem = product_elem.find(['p', 'div'], class_=['description', 'product-description', 'excerpt'])
                            description = desc_elem.get_text(strip=True) if desc_elem else f'Компрессорное оборудование {product_name}'

                            # Short description
                            short_desc = description[:200] if len(description) > 200 else description

                            self.stdout.write(f'    [+] {product_name}')

                            if not dry_run:
                                item, created = Item.objects.get_or_create(
                                    title=product_name,
                                    defaults={
                                        'slug': slugify(transliterate(product_name)),
                                        'category': category,
                                        'description': description,
                                        'short_description': short_desc,
                                        'status': 'published',
                                        'order': idx,
                                    }
                                )

                            products_count += 1

                            if products_count >= limit:
                                break

                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'    [!] Error parsing product: {str(e)}'))
                            continue

                    if products_count >= limit:
                        break

                    time.sleep(0.5)  # Be polite

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  [!] Error parsing category: {str(e)}'))
                    continue

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching chkz.kz: {str(e)}'))

        return products_count

    def scrape_ts2006(self, headers, dry_run, limit):
        """Scrape products from ts2006.kz"""
        base_url = 'https://ts2006.kz'

        products_count = 0

        # Define some known categories from the site
        categories_to_scrape = [
            {'name': 'Компрессоры', 'url': f'{base_url}/'},
            {'name': 'Промышленное оборудование', 'url': f'{base_url}/'},
        ]

        for cat_info in categories_to_scrape:
            try:
                category_name = cat_info['name']
                url = cat_info['url']

                self.stdout.write(f'  Category: {category_name}')

                if not dry_run:
                    category, created = Category.objects.get_or_create(
                        name=category_name,
                        defaults={
                            'slug': slugify(transliterate(category_name)),
                            'description': f'Категория {category_name}'
                        }
                    )

                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find product sections
                product_sections = soup.find_all(['div', 'article', 'section'], class_=['product', 'item', 'card'])

                if not product_sections:
                    # Try to find any structured content with headings
                    product_sections = soup.find_all(['div'], class_=['content', 'main'])

                for idx, section in enumerate(product_sections[:limit], 1):
                    try:
                        # Look for product names
                        name_elem = section.find(['h1', 'h2', 'h3', 'h4'])
                        if not name_elem:
                            continue

                        product_name = name_elem.get_text(strip=True)

                        if not product_name or len(product_name) < 3:
                            continue

                        # Avoid navigation items
                        if any(skip in product_name.lower() for skip in ['главная', 'контакты', 'о компании', 'menu', 'navigation']):
                            continue

                        # Extract description
                        desc_paragraphs = section.find_all('p')
                        description_parts = [p.get_text(strip=True) for p in desc_paragraphs if len(p.get_text(strip=True)) > 20]
                        description = ' '.join(description_parts[:3]) if description_parts else f'Промышленное оборудование {product_name}'

                        short_desc = description[:200] if len(description) > 200 else description

                        self.stdout.write(f'    [+] {product_name}')

                        if not dry_run:
                            item, created = Item.objects.get_or_create(
                                title=product_name,
                                defaults={
                                    'slug': slugify(transliterate(product_name)),
                                    'category': category,
                                    'description': description,
                                    'short_description': short_desc,
                                    'status': 'published',
                                    'order': idx,
                                }
                            )

                        products_count += 1

                        if products_count >= limit:
                            break

                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'    [!] Error parsing product: {str(e)}'))
                        continue

                if products_count >= limit:
                    break

                time.sleep(0.5)  # Be polite

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  [!] Error scraping category: {str(e)}'))
                continue

        return products_count
