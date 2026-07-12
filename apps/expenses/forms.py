from django import forms

from .models import Category, Expense

TAILWIND_INPUT = (
    "block w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm "
    "text-slate-900 placeholder:text-slate-400 shadow-sm focus:border-emerald-500 "
    "focus:ring-2 focus:ring-emerald-500/20 focus:outline-none transition"
)


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "date", "payment_method", "note"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.TextInput(attrs={"placeholder": "Optional note"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(owner__isnull=True) | Category.objects.filter(
                owner=user
            )
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": TAILWIND_INPUT})


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "icon"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": TAILWIND_INPUT})


class ExpenseFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(owner__isnull=True) | Category.objects.filter(
                owner=user
            )
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": TAILWIND_INPUT})
