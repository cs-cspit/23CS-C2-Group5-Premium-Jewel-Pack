from django import forms
from django.contrib.auth.models import User
from .models import Order, Address

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ("username", "email")

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        if User.objects.filter(username=cleaned.get("username")).exists():
            raise forms.ValidationError("Username already taken.")
        return cleaned

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
