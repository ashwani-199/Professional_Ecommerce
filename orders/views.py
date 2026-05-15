from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from store.models import Cart, CartItem
from .models import Order, OrderItem, Payment, Address
from .forms import AddressForm, CheckoutForm
import razorpay
import random
import string
import re
import time
import json


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
            elif payment_method == 'razorpay':
                return initiate_razorpay_payment(request, cart, address_id)
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


def initiate_razorpay_payment(request, cart, address_id):
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        messages.error(request, 'Razorpay is not configured. Please try a different payment method.')
        return redirect('orders:checkout')

    address = get_object_or_404(Address, id=address_id, user=request.user)
    total = cart.total()
    amount_paise = int(total * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        razorpay_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': f'receipt_{request.user.id}_{int(time.time())}',
            'payment_capture': '1',
        })
    except Exception as e:
        messages.error(request, f'Payment gateway error: {str(e)}')
        return redirect('orders:checkout')

    with transaction.atomic():
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

        Payment.objects.create(
            order=order,
            amount=total,
            success=False,
            payment_method='razorpay',
            razorpay_order_id=razorpay_order['id'],
            transaction_id=razorpay_order['id'],
        )

        cart.active = False
        cart.save()

    return render(request, 'orders/razorpay_payment.html', {
        'order': order,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order['id'],
        'amount': amount_paise,
        'currency': 'INR',
        'order_id': order.id,
    })


@login_required
def verify_razorpay_payment(request):
    if request.method != 'POST':
        return redirect('orders:order_list')

    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        messages.error(request, 'Invalid payment response.')
        return redirect('orders:order_list')

    try:
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found.')
        return redirect('orders:order_list')

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature,
    }

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature(params_dict)
        signature_valid = True
    except razorpay.errors.SignatureVerificationError:
        signature_valid = False

    if signature_valid:
        with transaction.atomic():
            for item in payment.order.items.all():
                product = item.product
                if product:
                    product.inventory -= item.quantity
                    product.save()

            payment.success = True
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save()

        messages.success(request, f'Order #{payment.order.id} placed successfully! Payment received via Razorpay.')
        return redirect('orders:order_confirmation', order_id=payment.order.id)
    else:
        payment.success = False
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.save()

        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('orders:order_detail', order_id=payment.order.id)


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
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method != 'POST':
        return redirect('orders:order_detail', order_id=order.id)

    if order.status not in ('pending', 'processing'):
        messages.error(request, 'This order cannot be canceled.')
        return redirect('orders:order_detail', order_id=order.id)

    with transaction.atomic():
        for item in order.items.all():
            product = item.product
            if product:
                product.inventory += item.quantity
                product.save()
        order.status = 'canceled'
        order.save()

    messages.success(request, f'Order #{order.id} has been canceled successfully.')
    return redirect('orders:order_detail', order_id=order.id)


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
