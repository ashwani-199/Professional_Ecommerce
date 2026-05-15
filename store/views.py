from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg
from django.conf import settings
from .models import Product, Category, Cart, CartItem
from .forms import ContactForm


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


def ads_txt(request):
    client_id = getattr(settings, 'ADSENSE_CLIENT_ID', '')
    if client_id:
        return HttpResponse(f"google.com, {client_id}, DIRECT, f08c47fec0942fa0\n", content_type="text/plain")
    return HttpResponse("", content_type="text/plain")


def robots_txt(request):
    lines = [
        "User-agent: *",
    ]
    if settings.DEBUG:
        lines.append("Disallow: /")
    else:
        lines.append("Disallow: /admin/")
        lines.append("Disallow: /accounts/")
        lines.append("Disallow: /cart/")
        lines.append("Disallow: /orders/")
        lines.append("")
        lines.append(f"Sitemap: {settings.SITE_URL}/sitemap.xml")
    return HttpResponse("\n".join(lines), content_type="text/plain")


def home(request):
    products = Product.objects.filter(is_active=True).prefetch_related('reviews')[:12]
    categories = Category.objects.all()
    return render(request, 'store/home.html', {
        'products': products,
        'categories': categories,
    })


def product_list(request):
    products = Product.objects.filter(is_active=True).prefetch_related('reviews')
    categories = Category.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related('images', 'reviews__user', 'sizes'),
        slug=slug, is_active=True
    )
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id).prefetch_related('reviews')[:4]

    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'user_review': user_review,
    })


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_active=True).prefetch_related('reviews')
    return render(request, 'store/category_products.html', {
        'category': category,
        'products': products,
    })


@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user, active=True)
    except Cart.DoesNotExist:
        cart = None
    return render(request, 'store/cart.html', {'cart': cart})


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to add items to cart.')
        return redirect('accounts:login')

    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    size_id = request.POST.get('size')

    if quantity > product.inventory:
        messages.error(request, 'Not enough stock available.')
        return redirect('store:product_detail', slug=product.slug)

    cart, _ = Cart.objects.get_or_create(user=request.user, active=True)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.inventory:
            messages.error(request, 'Not enough stock available.')
            return redirect('store:cart_detail')
        cart_item.quantity = new_quantity

    if size_id:
        from .models import Size
        try:
            cart_item.size = Size.objects.get(id=size_id)
        except Size.DoesNotExist:
            pass

    cart_item.save()
    messages.success(request, f'{product.title} added to cart.')
    return redirect('store:cart_detail')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if cart_item.cart.user == request.user:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    return redirect('store:cart_detail')


@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        if cart_item.cart.user == request.user:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > cart_item.product.inventory:
                messages.error(request, 'Not enough stock available.')
                return redirect('store:cart_detail')
            if quantity <= 0:
                cart_item.delete()
                messages.success(request, 'Item removed from cart.')
            else:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, 'Cart updated.')
        return redirect('store:cart_detail')
    return redirect('store:cart_detail')


@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = int(request.POST.get('rating', 0))
        title = request.POST.get('title', '')
        comment = request.POST.get('comment', '')

        if rating < 1 or rating > 5:
            messages.error(request, 'Rating must be between 1 and 5.')
            return redirect('store:product_detail', slug=product.slug)

        from .models import Review
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating, 'title': title, 'comment': comment}
        )
        messages.success(request, 'Review submitted successfully.')
    return redirect('store:product_detail', slug=product.slug)


def about(request):
    return render(request, 'store/about.html')


def blog(request):
    return render(request, 'store/blog.html')


def privacy(request):
    return render(request, 'store/privacy.html')


def terms(request):
    return render(request, 'store/terms.html')


def customers(request):
    return render(request, 'store/customers.html')


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            messages.success(
                request,
                'Thank you for your message! We will get back to you within 24 hours.'
            )
            return redirect('store:contact')
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'store/contact.html', {'form': form})


def faqs(request):
    return render(request, 'store/faqs.html')


def shipping(request):
    return render(request, 'store/shipping.html')


def refund(request):
    return render(request, 'store/refund.html')
