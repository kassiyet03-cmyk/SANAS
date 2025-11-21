import sys
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
    help = 'Fix slugs to use Latin characters instead of Cyrillic'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Fixing slugs...'))

        # Fix category slugs
        categories = Category.objects.all()
        for category in categories:
            old_slug = category.slug
            transliterated = transliterate(category.name)
            new_slug = slugify(transliterated)

            if old_slug != new_slug:
                category.slug = new_slug
                category.save()
                self.stdout.write(f'[+] Updated category: {category.name}')
                self.stdout.write(f'    Old slug: {old_slug} -> New slug: {new_slug}')

        # Fix item slugs
        items = Item.objects.all()
        for item in items:
            old_slug = item.slug
            transliterated = transliterate(item.title)
            new_slug = slugify(transliterated)

            if old_slug != new_slug:
                item.slug = new_slug
                item.save()
                self.stdout.write(f'[+] Updated item: {item.title}')
                self.stdout.write(f'    Old slug: {old_slug} -> New slug: {new_slug}')

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Slugs fixed!'))
        self.stdout.write(self.style.SUCCESS(f'Categories updated: {categories.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Items updated: {items.count()}'))
