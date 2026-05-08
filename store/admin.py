from django.contrib import admin
from .models import Category, Product, ProductImage, Size, Review, Cart, CartItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'discount_percent', 'sale_price_display', 'inventory', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    list_editable = ('is_active', 'inventory', 'discount_percent')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    filter_horizontal = ('sizes',)
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_percent')
        }),
        ('Product Details', {
            'fields': ('sizes', 'highlights', 'additional_info')
        }),
        ('Inventory', {
            'fields': ('inventory', 'is_active')
        }),
    )

    def sale_price_display(self, obj):
        if obj.discount_percent > 0:
            return f"₹{obj.sale_price():.2f}"
        return '-'
    sale_price_display.short_description = 'Sale Price'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main', 'alt_text')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__title', 'user__username', 'comment')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'active', 'created_at', 'updated_at')
    list_filter = ('active',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'size', 'quantity')
    list_filter = ('cart',)
