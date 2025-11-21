import sys
import os
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.images import ImageFile
from website.models import Item, Category
import time

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class Command(BaseCommand):
    help = 'Attempt to scrape images from chkz.kz website'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving images',
        )

    def download_image(self, url, item, dry_run=False):
        """Download and save image for an item"""
        try:
            # Ensure URL is absolute
            if url.startswith('/'):
                url = f'https://chkz.kz{url}'

            self.stdout.write(f'  Attempting to download: {url}')

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                self.stdout.write(f'  [!] Not an image: {content_type}')
                return False

            if dry_run:
                self.stdout.write(f'  [DRY RUN] Would save image for: {item.title}')
                return True

            # Create file name
            ext = url.split('.')[-1].split('?')[0]
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                ext = 'jpg'

            filename = f'{item.slug}.{ext}'

            # Save image to item
            image_file = ImageFile(BytesIO(response.content), name=filename)
            item.main_image = image_file
            item.save()

            self.stdout.write(self.style.SUCCESS(f'  [+] Image saved for: {item.title}'))
            return True

        except Exception as e:
            self.stdout.write(f'  [!] Failed: {str(e)}')
            return False

    def scrape_product_page(self, url):
        """Scrape a product page for image URLs"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for images in common patterns
            images = []

            # Find all img tags
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and 'picture.loading' not in src:
                    images.append(src)

            # Find images in picture tags
            for picture in soup.find_all('picture'):
                for source in picture.find_all('source'):
                    srcset = source.get('srcset')
                    if srcset:
                        images.append(srcset.split(',')[0].strip().split(' ')[0])

            return images

        except Exception as e:
            self.stdout.write(f'  [!] Failed to scrape {url}: {str(e)}')
            return []

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('Starting image scraping from chkz.kz...'))

        # Map of product names to their catalog URLs on chkz.kz
        product_urls = {
            'ДЭН "СТАНДАРТ"': '/catalog/vintovye_kompressornye_ustanovki_tipa_den_standart_/',
            'ДЭН "ОПТИМ"': '/catalog/vintovye_kompressornye_ustanovki_s_chastotnym_regulirovaniem_den_optim/',
            'ДЭН "ВОЛЬТ"': '/catalog/vintovye_kompressornye_ustanovki_s_vysokovoltnym_dvigatelem_den_volt/',
            'ДЭН "ШАХТЕР"': '/catalog/den_shm_shakhter/',
            'КВ (дизельные)': '/catalog/dizelnye_vintovye_kompressornye_ustanovki_tipa_kv/',
        }

        for product_name, catalog_url in product_urls.items():
            try:
                item = Item.objects.get(title=product_name, status='published')

                # Skip if already has image
                if item.main_image and not dry_run:
                    self.stdout.write(f'[SKIP] {product_name} already has an image')
                    continue

                self.stdout.write(f'\n[+] Processing: {product_name}')

                full_url = f'https://chkz.kz{catalog_url}'
                images = self.scrape_product_page(full_url)

                if images:
                    self.stdout.write(f'  Found {len(images)} images')
                    # Try to download the first valid image
                    for img_url in images:
                        if self.download_image(img_url, item, dry_run):
                            break
                else:
                    self.stdout.write('  [!] No images found on page')

                # Be nice to the server
                time.sleep(1)

            except Item.DoesNotExist:
                self.stdout.write(f'[!] Product not found: {product_name}')
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[!] Error processing {product_name}: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Image scraping completed!'))
