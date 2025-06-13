from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product, Category, ProductImage
from faker import Faker
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populates the database with mock products'

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        # Create categories
        categories = [
            'Electronics',
            'Clothing',
            'Books',
            'Home & Kitchen',
            'Sports & Outdoors',
            'Beauty & Personal Care',
            'Toys & Games',
            'Health & Household',
            'Automotive',
            'Garden & Outdoor'
        ]
        
        category_objects = []
        for category_name in categories:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'description': f'Products in {category_name} category'}
            )
            category_objects.append(category)
            self.stdout.write(f'Created category: {category_name}')

        # Product templates for different categories
        product_templates = {
            'Electronics': {
                'name_templates': [
                    '{brand} {model} {type}',
                    '{brand} {type} {model}',
                    '{brand} {model} Series {type}'
                ],
                'price_range': (50, 2000),
                'specifications': {
                    'brand': ['Samsung', 'Apple', 'Sony', 'LG', 'Dell', 'HP', 'Asus'],
                    'model': ['Pro', 'Elite', 'Ultra', 'Max', 'Plus', 'Lite'],
                    'type': ['Smartphone', 'Laptop', 'Tablet', 'Smartwatch', 'Headphones']
                }
            },
            'Clothing': {
                'name_templates': [
                    '{brand} {type} {style}',
                    '{brand} {style} {type}',
                    '{brand} {type} Collection'
                ],
                'price_range': (20, 200),
                'specifications': {
                    'brand': ['Nike', 'Adidas', 'Zara', 'H&M', 'Gap', 'Levi\'s'],
                    'style': ['Casual', 'Formal', 'Sport', 'Vintage', 'Modern'],
                    'type': ['T-Shirt', 'Jeans', 'Dress', 'Jacket', 'Shoes']
                }
            },
            'Books': {
                'name_templates': [
                    '{title} by {author}',
                    '{title}: {subtitle}',
                    '{title} ({genre})'
                ],
                'price_range': (10, 50),
                'specifications': {
                    'author': ['John Smith', 'Jane Doe', 'Robert Johnson', 'Emily Brown'],
                    'genre': ['Fiction', 'Non-Fiction', 'Mystery', 'Science Fiction'],
                    'format': ['Hardcover', 'Paperback', 'E-Book']
                }
            }
        }

        # Combine all product templates
        all_templates = []
        for category, template in product_templates.items():
            all_templates.extend([(category, template)] * 3)  # Weight each category equally

        # Create products
        with transaction.atomic():
            for i in range(100):  # Create 100 products
                category, template = random.choice(all_templates)
                
                # Generate product name
                name_template = random.choice(template['name_templates'])
                name = name_template.format(
                    brand=random.choice(template['specifications']['brand']),
                    model=random.choice(template['specifications']['model']) if 'model' in template['specifications'] else '',
                    type=random.choice(template['specifications']['type']),
                    title=fake.catch_phrase(),
                    author=random.choice(template['specifications']['author']) if 'author' in template['specifications'] else '',
                    subtitle=fake.sentence(),
                    genre=random.choice(template['specifications']['genre']) if 'genre' in template['specifications'] else '',
                    style=random.choice(template['specifications']['style']) if 'style' in template['specifications'] else ''
                )

                # Create product
                product = Product.objects.create(
                    name=name,
                    description=fake.paragraph(),
                    price=Decimal(str(random.uniform(*template['price_range']))).quantize(Decimal('0.01')),
                    category=random.choice(category_objects),
                    stock=random.randint(0, 100),
                    rating=random.uniform(1, 5),
                    specifications={
                        'brand': random.choice(template['specifications']['brand']),
                        'model': random.choice(template['specifications']['model']) if 'model' in template['specifications'] else None,
                        'type': random.choice(template['specifications']['type']),
                        'color': fake.color_name(),
                        'weight': f"{random.uniform(0.1, 5.0):.1f} kg",
                        'dimensions': f"{random.randint(10, 100)}x{random.randint(10, 100)}x{random.randint(10, 100)} cm"
                    }
                )

                # Create product images
                for j in range(random.randint(1, 4)):
                    ProductImage.objects.create(
                        product=product,
                        image=f'products/default_{random.randint(1, 5)}.jpg',
                        is_primary=(j == 0)
                    )

                self.stdout.write(f'Created product: {name}')

        self.stdout.write(self.style.SUCCESS('Successfully populated database with mock products')) 