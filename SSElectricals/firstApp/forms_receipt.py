from django import forms
from django.forms import inlineformset_factory
from .models import OfflineReceipt, ReceiptItem


class ReceiptForm(forms.ModelForm):
    """Form for creating/editing offline receipts"""
    
    class Meta:
        model = OfflineReceipt
        fields = [
            'buyer_name', 'buyer_email', 'buyer_phone', 'buyer_address',
            'shop_name', 'shop_address', 'shop_phone', 'shop_gst',
            'subtotal', 'tax_amount', 'discount_amount', 'grand_total',
            'notes'
        ]
        widgets = {
            'buyer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer Name',
                'required': True
            }),
            'buyer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'customer@example.com (Optional - links to account)'
            }),
            'buyer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 XXXXXXXXXX'
            }),
            'buyer_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Street, Area, City'
            }),
            'shop_name': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'shop_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'readonly': 'readonly'
            }),
            'shop_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'shop_gst': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GST Number (Optional)'
            }),
            'subtotal': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': 'readonly',
                'id': 'id_subtotal'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'id_tax'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'id_discount'
            }),
            'grand_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': 'readonly',
                'id': 'id_grand_total'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal notes (not visible on receipt)'
            })
        }


class ReceiptItemForm(forms.ModelForm):
    """Form for individual receipt line items"""
    
    class Meta:
        model = ReceiptItem
        fields = ['item_name', 'quantity', 'unit_price', 'description']
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'form-control product-datalist-input',
                'placeholder': 'Type to search products...',
                'list': 'product-list',
                'autocomplete': 'off'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'value': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Additional details (optional)'
            })
        }


# Formset for dynamic item rows
ReceiptItemFormSet = inlineformset_factory(
    OfflineReceipt,
    ReceiptItem,
    form=ReceiptItemForm,
    extra=3,  # Start with 3 empty rows
    can_delete=True,
    min_num=1,  # At least 1 item required
    validate_min=True
)


class VoidReceiptForm(forms.Form):
    """Form for voiding a receipt"""
    
    VOID_REASONS = [
        ('duplicate', 'Duplicate Entry'),
        ('error', 'Data Entry Error'),
        ('cancelled', 'Sale Cancelled'),
        ('customer_request', 'Customer Request'),
        ('other', 'Other Reason')
    ]
    
    reason_type = forms.ChoiceField(
        choices=VOID_REASONS,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Reason for Voiding'
    )
    
    reason_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Provide additional details...',
            'required': True
        }),
        label='Details',
        help_text='Explain why this receipt is being voided'
    )
    
    confirm = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': True
        }),
        label='I confirm this receipt should be voided',
        help_text='This action cannot be undone'
    )


class ReceiptFilterForm(forms.Form):
    """Form for filtering receipt history"""
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('ACTIVE', 'Active'),
        ('VOID', 'Void'),
        ('CORRECTED', 'Corrected')
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    financial_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2024-25'
        })
    )
    
    buyer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by customer name'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
