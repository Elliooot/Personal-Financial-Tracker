from django import forms
from finance.models import Currency, Account, Category, Transaction, Budget

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