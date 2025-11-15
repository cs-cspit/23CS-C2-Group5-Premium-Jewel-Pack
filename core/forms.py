from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Order, Address, Product, UserProfile

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'short_description', 'description', 'price', 'stock', 'image', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

class SignupForm(UserCreationForm):
    # Custom fields for your business requirements
    full_name = forms.CharField(
        max_length=100, 
        required=True,
        label="Name",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your full name"})
    )
    firm_name = forms.CharField(
        max_length=100, 
        required=True,
        label="Firm Name", 
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your firm/company name"})
    )
    mobile_number = forms.CharField(
        max_length=15, 
        required=True,
        label="Mobile Number",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your mobile number"})
    )
    address = forms.CharField(
        required=True,
        label="Address",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter your complete address"})
    )
    email = forms.EmailField(
        required=True, 
        label="Email Address",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email address"})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the default fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Confirm password'
        })
        
        # Update labels
        self.fields['password1'].label = "Password"
        self.fields['password2'].label = "Confirm Password"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["full_name"]
        if commit:
            user.save()
            # Create UserProfile with additional information
            UserProfile.objects.create(
                user=user,
                firm_name=self.cleaned_data["firm_name"],
                mobile_number=self.cleaned_data["mobile_number"],
                address=self.cleaned_data["address"]
            )
        return user
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("full_name","email","phone","address_line1","address_line2","city","state","postal_code","country")
        widgets = {
            "full_name": forms.TextInput(attrs={"class":"form-control"}),
            "email": forms.EmailInput(attrs={"class":"form-control"}),
            "phone": forms.TextInput(attrs={"class":"form-control"}),
            "address_line1": forms.TextInput(attrs={"class":"form-control"}),
            "address_line2": forms.TextInput(attrs={"class":"form-control"}),
            "city": forms.TextInput(attrs={"class":"form-control"}),
            "state": forms.TextInput(attrs={"class":"form-control"}),
            "postal_code": forms.TextInput(attrs={"class":"form-control"}),
            "country": forms.TextInput(attrs={"class":"form-control"}),
        }

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("full_name","phone","address_line1","address_line2","city","state","postal_code","country")
        widgets = {f: forms.TextInput(attrs={"class":"form-control"}) for f in fields}
