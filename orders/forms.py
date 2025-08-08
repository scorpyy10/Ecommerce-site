from django import forms
from .models import Order


class AddressForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'delivery_first_name', 'delivery_last_name', 'delivery_company',
            'delivery_address_line_1', 'delivery_address_line_2',
            'delivery_city', 'delivery_state', 'delivery_postal_code',
            'delivery_country', 'delivery_phone', 'delivery_instructions',
            'preferred_delivery_time'
        ]
        
        widgets = {
            'delivery_first_name': forms.TextInput(attrs={
                'placeholder': 'First Name',
                'required': True
            }),
            'delivery_last_name': forms.TextInput(attrs={
                'placeholder': 'Last Name',
                'required': True
            }),
            'delivery_company': forms.TextInput(attrs={
                'placeholder': 'Company (Optional)'
            }),
            'delivery_address_line_1': forms.TextInput(attrs={
                'placeholder': 'Street Address',
                'required': True
            }),
            'delivery_address_line_2': forms.TextInput(attrs={
                'placeholder': 'Apt, Suite, Building (Optional)'
            }),
            'delivery_city': forms.TextInput(attrs={
                'placeholder': 'City',
                'required': True
            }),
            'delivery_state': forms.TextInput(attrs={
                'placeholder': 'State/Province',
                'required': True
            }),
            'delivery_postal_code': forms.TextInput(attrs={
                'placeholder': 'Postal/ZIP Code',
                'required': True
            }),
            'delivery_country': forms.Select(attrs={
                'required': True
            }),
            'delivery_phone': forms.TextInput(attrs={
                'placeholder': '+91 9876543210',
                'required': True
            }),
            'delivery_instructions': forms.Textarea(attrs={
                'placeholder': 'Special delivery instructions (Optional)',
                'rows': 3
            }),
            'preferred_delivery_time': forms.Select(attrs={
                'required': True
            })
        }
        
        labels = {
            'delivery_first_name': 'First Name *',
            'delivery_last_name': 'Last Name *',
            'delivery_company': 'Company',
            'delivery_address_line_1': 'Street Address *',
            'delivery_address_line_2': 'Apartment, Suite, etc.',
            'delivery_city': 'City *',
            'delivery_state': 'State/Province *',
            'delivery_postal_code': 'Postal Code *',
            'delivery_country': 'Country *',
            'delivery_phone': 'Phone Number *',
            'delivery_instructions': 'Delivery Instructions',
            'preferred_delivery_time': 'Preferred Delivery Time *'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name == 'delivery_instructions':
                field.widget.attrs['class'] = 'form-control'
            elif field_name in ['delivery_country', 'preferred_delivery_time']:
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        
        # Set default country
        self.fields['delivery_country'].initial = 'India'
        
        # Add country choices
        self.fields['delivery_country'].widget.choices = [
            ('India', 'India'),
            ('United States', 'United States'),
            ('United Kingdom', 'United Kingdom'),
            ('Canada', 'Canada'),
            ('Australia', 'Australia'),
            ('Germany', 'Germany'),
            ('France', 'France'),
            ('Other', 'Other')
        ]
        
        # Pre-fill with user data if available
        if user and user.is_authenticated:
            if user.first_name and not self.initial.get('delivery_first_name'):
                self.fields['delivery_first_name'].initial = user.first_name
            if user.last_name and not self.initial.get('delivery_last_name'):
                self.fields['delivery_last_name'].initial = user.last_name
            if user.email and not self.initial.get('delivery_phone'):
                # You could add phone to User model or profile later
                pass
    
    def clean_delivery_phone(self):
        phone = self.cleaned_data.get('delivery_phone')
        if phone:
            # Remove all non-digit characters for validation
            digits_only = ''.join(filter(str.isdigit, phone))
            if len(digits_only) < 10:
                raise forms.ValidationError('Please enter a valid phone number with at least 10 digits.')
        return phone
    
    def clean_delivery_postal_code(self):
        postal_code = self.cleaned_data.get('delivery_postal_code')
        country = self.cleaned_data.get('delivery_country')
        
        if postal_code and country == 'India':
            # Indian postal code validation (6 digits)
            digits_only = ''.join(filter(str.isdigit, postal_code))
            if len(digits_only) != 6:
                raise forms.ValidationError('Indian postal codes must be 6 digits.')
        
        return postal_code
