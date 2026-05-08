from django.core.management.base import BaseCommand
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Seeds the database with sample products'

    def handle(self, *args, **options):
        categories_data = [
            {'name': 'Electronics', 'slug': 'electronics', 'description': 'Latest gadgets and electronics'},
            {'name': 'Clothing', 'slug': 'clothing', 'description': 'Fashion and apparel'},
            {'name': 'Books', 'slug': 'books', 'description': 'Books, eBooks and publications'},
            {'name': 'Home & Garden', 'slug': 'home-garden', 'description': 'Home improvement and garden'},
            {'name': 'Sports', 'slug': 'sports', 'description': 'Sports equipment and accessories'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name'], 'description': cat_data['description']}
            )
            categories[cat_data['slug']] = cat
            self.stdout.write(f'Created category: {cat.name}')

        products_data = [
            {'title': 'Wireless Bluetooth Headphones', 'slug': 'wireless-headphones', 'category': 'electronics', 'price': 79.99, 'inventory': 50, 'description': 'High-quality wireless headphones with noise cancellation and 20-hour battery life.'},
            {'title': 'Smart Watch Pro', 'slug': 'smart-watch-pro', 'category': 'electronics', 'price': 299.99, 'inventory': 30, 'description': 'Advanced smartwatch with health monitoring, GPS, and water resistance.'},
            {'title': 'Laptop Stand Ergonomic', 'slug': 'laptop-stand', 'category': 'electronics', 'price': 49.99, 'inventory': 100, 'description': 'Adjustable aluminum laptop stand for better posture and cooling.'},
            {'title': 'USB-C Hub 7-in-1', 'slug': 'usb-c-hub', 'category': 'electronics', 'price': 39.99, 'inventory': 75, 'description': 'Multi-port USB-C hub with HDMI, USB 3.0, and card reader.'},
            {'title': 'Mechanical Gaming Keyboard', 'slug': 'gaming-keyboard', 'category': 'electronics', 'price': 129.99, 'inventory': 40, 'description': 'RGB mechanical keyboard with blue switches and programmable macros.'},
            
            {'title': 'Cotton T-Shirt Pack', 'slug': 'cotton-tshirt-pack', 'category': 'clothing', 'price': 29.99, 'inventory': 200, 'description': 'Pack of 3 premium cotton t-shirts in assorted colors.'},
            {'title': 'Denim Jeans Slim Fit', 'slug': 'denim-jeans', 'category': 'clothing', 'price': 59.99, 'inventory': 80, 'description': 'Classic slim fit denim jeans in dark wash.'},
            {'title': 'Winter Jacket', 'slug': 'winter-jacket', 'category': 'clothing', 'price': 149.99, 'inventory': 25, 'description': 'Warm winter jacket with hood and waterproof exterior.'},
            {'title': 'Running Shoes', 'slug': 'running-shoes', 'category': 'clothing', 'price': 89.99, 'inventory': 60, 'description': 'Lightweight running shoes with cushioned sole.'},
            {'title': 'Wool Sweater', 'slug': 'wool-sweater', 'category': 'clothing', 'price': 79.99, 'inventory': 45, 'description': 'Soft merino wool sweater for cold weather.'},
            
            {'title': 'Python Programming Book', 'slug': 'python-book', 'category': 'books', 'price': 49.99, 'inventory': 100, 'description': 'Comprehensive guide to Python programming for beginners.'},
            {'title': 'The Art of Thinking', 'slug': 'art-thinking', 'category': 'books', 'price': 19.99, 'inventory': 150, 'description': 'Classic self-help book on developing critical thinking skills.'},
            {'title': 'Cookbook Collection', 'slug': 'cookbook', 'category': 'books', 'price': 34.99, 'inventory': 60, 'description': 'Collection of 200 easy and delicious recipes.'},
            
            {'title': 'LED Desk Lamp', 'slug': 'led-desk-lamp', 'category': 'home-garden', 'price': 35.99, 'inventory': 90, 'description': 'Adjustable LED desk lamp with multiple brightness levels.'},
            {'title': 'Plant Pot Set', 'slug': 'plant-pot-set', 'category': 'home-garden', 'price': 24.99, 'inventory': 70, 'description': 'Set of 3 ceramic plant pots in modern design.'},
            {'title': 'Throw Pillow Set', 'slug': 'throw-pillows', 'category': 'home-garden', 'price': 39.99, 'inventory': 55, 'description': 'Set of 4 decorative throw pillows.'},
            
            {'title': 'Yoga Mat Premium', 'slug': 'yoga-mat', 'category': 'sports', 'price': 34.99, 'inventory': 120, 'description': 'Non-slip yoga mat with carrying strap.'},
            {'title': 'Dumbbell Set', 'slug': 'dumbbell-set', 'category': 'sports', 'price': 89.99, 'inventory': 35, 'description': 'Adjustable dumbbell set 5-25 lbs.'},
            {'title': 'Tennis Racket', 'slug': 'tennis-racket', 'category': 'sports', 'price': 79.99, 'inventory': 40, 'description': 'Professional grade tennis racket with cover.'},
            {'title': 'Soccer Ball', 'slug': 'soccer-ball', 'category': 'sports', 'price': 24.99, 'inventory': 80, 'description': 'Official size soccer ball with pump.'},
        ]

        for prod_data in products_data:
            category = categories[prod_data['category']]
            Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults={
                    'title': prod_data['title'],
                    'category': category,
                    'price': prod_data['price'],
                    'inventory': prod_data['inventory'],
                    'description': prod_data['description'],
                    'is_active': True
                }
            )
            self.stdout.write(f'Created product: {prod_data["title"]}')

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with sample products!'))
