from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

from finance.models import Category, Account, Currency
from finance.forms import CategoryForm, TransactionForm

class CategoryFormTest(TestCase):
    def test_category_form_no_data(self):
        """Test the validation result when CategoryForm does not provide data"""
        user = get_user_model().objects.create_user(
            username=f'testuser-{uuid.uuid4()}',
            email=f'test-{uuid.uuid4()}@example.com',
            password='testpass123'
        )
        
        form = CategoryForm(data={}, user=user)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
    
    def test_category_form_valid_data(self):
        """Test the validation results when CategoryForm provides valid data"""
        user = get_user_model().objects.create_user(
            username=f'testuser-{uuid.uuid4()}',
            email=f'test-{uuid.uuid4()}@example.com',
            password='testpass123'
        )
        
        category_name = f'Category-{uuid.uuid4()}'
        
        form_data = {
            'name': category_name,
            'is_income': True
        }
        
        form = CategoryForm(data=form_data, user=user)
        form.instance.user = user  # Simulate setting the user attribute in the view
        
        self.assertTrue(form.is_valid())

class TransactionFormTest(TestCase):
    def setUp(self):
        """Set up common test data for transaction form tests"""
        username = f'testuser-{uuid.uuid4()}'
        email = f'test-{uuid.uuid4()}@example.com'
        
        # Get or create user
        self.user, _ = get_user_model().objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'password': 'testpass123'
            }
        )
        
        # Use get_or_create for currency
        self.currency, _ = Currency.objects.get_or_create(
            user=None,  # System currency
            currency_code='GBP',
            defaults={'exchange_rate': Decimal('1.0')}
        )
        
        # Use get_or_create for categories
        self.expense_category, _ = Category.objects.get_or_create(
            user=self.user,
            name='Food',
            defaults={'is_income': False}
        )
        
        self.income_category, _ = Category.objects.get_or_create(
            user=self.user,
            name='Salary',
            defaults={'is_income': True}
        )
        
        # Use get_or_create for account
        self.account, _ = Account.objects.get_or_create(
            user=self.user,
            account_name='Checking Account',
            defaults={
                'account_type': 'Bank',
                'balance': Decimal('1000.00'),
                'order': 1
            }
        )
    
    def test_transaction_form_no_data(self):
        """Test TransactionForm validation with no data"""
        form = TransactionForm(data={}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertGreaterEqual(len(form.errors), 5)  # At least date, category, transaction_type, amount, account
    
    def test_expense_transaction_valid_data(self):
        """Test valid expense transaction data"""
        form_data = {
            'date': '2024-03-20',
            'category': self.expense_category.id,
            'transaction_type': False,  # Expense
            'currency': self.currency.id,
            'amount': Decimal('45.99'),
            'account': self.account.id,
            'description': 'Grocery shopping'
        }
        
        form = TransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_income_transaction_valid_data(self):
        """Test valid income transaction data"""
        form_data = {
            'date': '2024-03-22',
            'category': self.income_category.id,
            'transaction_type': True,  # Income
            'currency': self.currency.id,
            'amount': Decimal('2500.00'),
            'account': self.account.id,
            'description': 'Monthly salary'
        }
        
        form = TransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_transaction_form_queryset_filtering(self):
        """Test that transaction form filters categories and accounts by user"""
        # Get or create another user with their own data
        other_username = f'otheruser-{uuid.uuid4()}'
        other_email = f'other-{uuid.uuid4()}@example.com'
        
        other_user, _ = get_user_model().objects.get_or_create(
            username=other_username,
            defaults={
                'email': other_email,
                'password': 'testpass123'
            }
        )
        
        # Get or create category for other user
        other_category, _ = Category.objects.get_or_create(
            user=other_user,
            name='Entertainment',
            defaults={'is_income': False}
        )
        
        # Get or create account for other user
        other_account, _ = Account.objects.get_or_create(
            user=other_user,
            account_name='Other Account',
            defaults={
                'account_type': 'Savings',
                'balance': Decimal('5000.00'),
                'order': 1
            }
        )
        
        # Initialize form for our main test user
        form = TransactionForm(user=self.user)
        
        # Check category queryset filtering
        self.assertIn(self.expense_category, form.fields['category'].queryset)
        self.assertIn(self.income_category, form.fields['category'].queryset)
        self.assertNotIn(other_category, form.fields['category'].queryset)
        
        # Check account queryset filtering
        self.assertIn(self.account, form.fields['account'].queryset)
        self.assertNotIn(other_account, form.fields['account'].queryset)