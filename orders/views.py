from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from store.models import Cart, CartItem
from .models import Order, OrderItem, Payment, Address
from .forms import AddressForm, CheckoutForm
import random
import string
import re


def generate_transaction_id():
    return 'TXN-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


def luhn_check(card_number):
    cleaned = card_number.replace(' ', '').replace('-', '')
    total = 0
    reverse_digits = cleaned[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user, active=True)
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('store:cart_detail')
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty.')
        return redirect('store:cart_detail')

    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            address_id = form.cleaned_data['address'].id
            payment_method = form.cleaned_data['payment_method']

            if payment_method in ('credit_card', 'stripe'):
                card_number = form.cleaned_data['card_number'].replace(' ', '').replace('-', '')
                return process_payment(request, cart, payment_method, card_number, address_id)
            else:
                return process_order(request, cart, address_id, payment_method)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CheckoutForm(user=request.user)
        if addresses.exists():
            form.fields['address'].initial = addresses.first()

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'addresses': addresses,
        'form': form,
    })


def process_order(request, cart, address_id, payment_method):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    with transaction.atomic():
        total = cart.total()
        order = Order.objects.create(
            user=request.user,
            address=address,
            total=total,
            status='pending'
        )

        for item in cart.items.all():
            if item.product.inventory < item.quantity:
                messages.error(request, f'{item.product.title} is out of stock.')
                return redirect('store:cart_detail')

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                size=item.size.name if item.size else None
            )
            item.product.inventory -= item.quantity
            item.product.save()

        Payment.objects.create(
            order=order,
            amount=total,
            success=True,
            payment_method=payment_method,
            transaction_id=generate_transaction_id()
        )

        cart.active = False
        cart.save()

    messages.success(request, f'Order #{order.id} placed successfully!')
    return redirect('orders:order_confirmation', order_id=order.id)


def process_payment(request, cart, payment_method, card_number, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    card_last4 = card_number[-4:]

    if card_number[0] == '4':
        card_brand = 'Visa'
    elif card_number[0] == '5':
        card_brand = 'Mastercard'
    elif card_number[0] == '3':
        card_brand = 'American Express'
    else:
        card_brand = 'Card'

    with transaction.atomic():
        total = cart.total()
        order = Order.objects.create(
            user=request.user,
            address=address,
            total=total,
            status='processing'
        )

        for item in cart.items.all():
            if item.product.inventory < item.quantity:
                messages.error(request, f'{item.product.title} is out of stock.')
                return redirect('store:cart_detail')

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                size=item.size.name if item.size else None
            )
            item.product.inventory -= item.quantity
            item.product.save()

        Payment.objects.create(
            order=order,
            amount=total,
            success=True,
            payment_method=payment_method,
            transaction_id=generate_transaction_id(),
            card_last4=card_last4,
            card_brand=card_brand
        )

        cart.active = False
        cart.save()

    messages.success(request, f'Order #{order.id} placed successfully! Payment received.')
    return redirect('orders:order_confirmation', order_id=order.id)


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/confirmation.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, 'Address added successfully.')
            return redirect('orders:checkout')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm()
    return render(request, 'orders/add_address.html', {'form': form})


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, 'Address updated successfully.')
            return redirect('orders:address_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm(instance=address)
    return render(request, 'orders/edit_address.html', {'form': form, 'address': address})


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully.')
    return redirect('orders:address_list')


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'orders/address_list.html', {'addresses': addresses})
