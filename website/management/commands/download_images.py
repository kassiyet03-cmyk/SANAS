import sys
import os
import requests
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.images import ImageFile
from website.models import Item

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class Command(BaseCommand):
    help = 'Download generic compressor images for products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='unsplash',
            help='Image source: unsplash (default)',
        )

    def handle(self, *args, **options):
        source = options['source']

        self.stdout.write(self.style.SUCCESS('Downloading images for products...'))

        # Generic compressor/industrial equipment images from Unsplash
        # These are high-quality, free-to-use images
        image_urls = {
            'compressor': [
                'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=800',  # Industrial equipment
                'https://images.unsplash.com/photo-1565015592401-6ea138c974d7?w=800',  # Machinery
                'https://images.unsplash.com/photo-1504222490345-c075b6008014?w=800',  # Industrial
                'https://images.unsplash.com/photo-1513828583688-c52646db42da?w=800',  # Equipment
                'https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=800',  # Factory
            ]
        }

        items = Item.objects.filter(status='published', main_image='')

        if not items.exists():
            self.stdout.write(self.style.WARNING('No items without images found.'))
            return

        image_index = 0
        total_images = len(image_urls['compressor'])

        for item in items:
            try:
                # Cycle through available images
                image_url = image_urls['compressor'][image_index % total_images]
                image_index += 1

                self.stdout.write(f'Downloading image for: {item.title}')

                # Download image
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()

                # Create file name
                filename = f'{item.slug}.jpg'

                # Save image to item
                image_file = ImageFile(BytesIO(response.content), name=filename)
                item.main_image = image_file
                item.save()

                self.stdout.write(self.style.SUCCESS(f'  [+] Image saved for: {item.title}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [!] Failed to download image for {item.title}: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'\n[SUCCESS] Downloaded images for {items.count()} products!'))
