from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).prefetch_related('images')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('store:product_detail', args=[obj.slug])


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse('store:category_products', args=[obj.slug])


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return [
            'store:home', 'store:product_list',
            'store:about', 'store:blog', 'store:customers',
            'store:contact', 'store:faqs',
            'store:shipping', 'store:refund',
            'store:privacy', 'store:terms',
        ]

    def location(self, item):
        return reverse(item)
