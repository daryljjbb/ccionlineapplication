from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Agency, Customer, Carrier, Policy

class UserAdminCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if isinstance(self.fields[field_name].widget, (forms.TextInput, forms.EmailInput)):
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})
            elif isinstance(self.fields[field_name].widget, forms.CheckboxInput):
                 self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})

class UserAdminChangeForm(UserChangeForm):
    password = None # Hide the password hash from the edit form
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if isinstance(self.fields[field_name].widget, (forms.TextInput, forms.EmailInput)):
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})
            elif isinstance(self.fields[field_name].widget, forms.CheckboxInput):
                 self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})

class AgencyForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['name', 'address', 'phone_number', 'email', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'address',
            'status', 'source', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Add a sticky note for this customer...'}),
        }

class CarrierForm(forms.ModelForm):
    class Meta:
        model = Carrier
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = { 'is_active': 'Active' }



class PolicyForm(forms.ModelForm):
    carrier = forms.ModelChoiceField(queryset=Carrier.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Policy
        fields = [
            'carrier', 'policy_number', 'effective_date', 'expiration_date',
            'premium_amount', 'agency_fee', 'status'
        ]
        widgets = {
            'policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # This is the carrier premium, calculated by JS
            'premium_amount': forms.NumberInput(attrs={'class': 'form-control', 'id': 'premium-amount-input', 'readonly': True}),
            'agency_fee': forms.NumberInput(attrs={'class': 'form-control', 'id': 'agency-fee-input', 'step': '0.01', 'value': '0.00'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }