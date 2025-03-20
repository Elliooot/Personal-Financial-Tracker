from django import forms
from finance.models import Currency, Account, Category, Transaction, Budget
from django.utils.translation import gettext_lazy as _
from datetime import datetime

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'category', 'transaction_type', 'currency', 'amount', 'account', 'description']
        
    def __init__(self, *args, **kwargs):
        # Correctly extract the user parameter
        self.user = kwargs.pop('user', None)
        # Call the parent init method with the remaining arguments
        super().__init__(*args, **kwargs)
        
        # If user is provided, restrict choices for category and account
        if self.user:
            self.fields['category'].queryset = Category.objects.filter(user=self.user)
            self.fields['account'].queryset = Account.objects.filter(user=self.user)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'is_income']

    def __init__(self, *args, **kwargs):
        # Extract the user parameter
        self.user = kwargs.pop('user', None)
        # Call the parent init method
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        category_name = cleaned_data.get('name')
        is_income = cleaned_data.get('is_income')
        
        if Category.objects.filter(
            user=self.instance.user if self.instance.pk else self.user,
            name=category_name,
            is_income=is_income
        ).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            raise forms.ValidationError('A category with this name already exists.')
        
        return cleaned_data


class BudgetForm(forms.ModelForm):
    period = forms.CharField(required=True, widget=forms.TextInput(attrs={'type': 'month'}))
    
    class Meta:
        model = Budget
        fields = ['category', 'budget_amount', 'period']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Only show expense categories for budgets
            self.fields['category'].queryset = Category.objects.filter(user=self.user, is_income=False)
    
    def clean_period(self):
        period = self.cleaned_data.get('period')
        try:
            # Convert YYYY-MM to a date object (first day of month)
            period_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
            return period_date
        except ValueError:
            raise forms.ValidationError(_("Invalid period format. Use YYYY-MM."))


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['currency_code', 'exchange_rate']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_currency_code(self):
        currency_code = self.cleaned_data.get('currency_code')
        if Currency.objects.filter(
            currency_code=currency_code
        ).exists():
            raise forms.ValidationError(_("This currency already exists."))
        return currency_code


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_name', 'account_type', 'balance']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_account_name(self):
        account_name = self.cleaned_data.get('account_name')
        if Account.objects.filter(
            user=self.user,
            account_name=account_name
        ).exists():
            raise forms.ValidationError(_("An account with this name already exists."))
        return account_name