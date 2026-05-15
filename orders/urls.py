from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('razorpay/verify/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('address/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('addresses/', views.address_list, name='address_list'),
]
