from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User

CURRENCY_CHOICES = [
    ("BDT", "BDT — Bangladeshi Taka"),
    ("USD", "USD — US Dollar"),
    ("EUR", "EUR — Euro"),
    ("GBP", "GBP — British Pound"),
    ("INR", "INR — Indian Rupee"),
]

TAILWIND_INPUT = (
    "block w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm "
    "text-slate-900 placeholder:text-slate-400 shadow-sm focus:border-emerald-500 "
    "focus:ring-2 focus:ring-emerald-500/20 focus:outline-none transition"
)


class SignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True)
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial="BDT")

    class Meta:
        model = User
        fields = ("full_name", "email", "currency", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": TAILWIND_INPUT, "placeholder": field.label})

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": TAILWIND_INPUT, "placeholder": "Email", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update({"class": TAILWIND_INPUT, "placeholder": "Password"})


class ProfileForm(forms.ModelForm):
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES)

    class Meta:
        model = User
        fields = ("full_name", "email", "currency")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": TAILWIND_INPUT})
