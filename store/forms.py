from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'John Doe',
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'john@example.com',
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition'
        })
    )
    subject = forms.ChoiceField(
        choices=[
            ('', 'Select a topic...'),
            ('order', 'Order Inquiry'),
            ('shipping', 'Shipping Question'),
            ('return', 'Return & Refund'),
            ('product', 'Product Information'),
            ('account', 'Account Issue'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition bg-white'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'How can we help you?',
            'rows': 5,
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition resize-none'
        })
    )
