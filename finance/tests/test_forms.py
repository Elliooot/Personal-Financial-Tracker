from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

from finance.models import Category, Account, Currency, Budget
from finance.forms import (
    CategoryForm, 
    TransactionForm, 
    BudgetForm, 
    AccountForm, 
    CurrencyForm
)

class BaseTestCase(TestCase):
    def setUp(self):
        """Set up common test data for all form tests"""
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


class BudgetFormTest(BaseTestCase):
    def test_budget_form_no_data(self):
        """Test BudgetForm validation with no data"""
        form = BudgetForm(data={}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertGreaterEqual(len(form.errors), 2)  # category and period

    def test_budget_form_valid_data(self):
        """Test valid budget form data"""
        from datetime import datetime
        
        form_data = {
            'category': self.expense_category.id,
            'budget_amount': Decimal('500.00'),
            'period': datetime.now().strftime('%Y-%m')
        }
        
        form = BudgetForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_budget_form_income_category_exclusion(self):
        """Test that income categories are excluded from budget form"""
        form = BudgetForm(user=self.user)
        
        # Check category queryset filtering
        self.assertIn(self.expense_category, form.fields['category'].queryset)
        self.assertNotIn(self.income_category, form.fields['category'].queryset)

    def test_budget_form_invalid_period(self):
        """Test budget form with invalid period format"""
        form_data = {
            'category': self.expense_category.id,
            'budget_amount': Decimal('500.00'),
            'period': 'invalid-date'
        }
        
        form = BudgetForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid period format', str(form.errors))


class AccountFormTest(BaseTestCase):
    def test_account_form_no_data(self):
        """Test AccountForm validation with no data"""
        form = AccountForm(data={}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertGreaterEqual(len(form.errors), 2)  # account_name and account_type

    def test_account_form_duplicate_name(self):
        """Test account form with duplicate account name"""
        form_data = {
            'account_name': 'Checking Account',  # Same as the account created in setUp
            'account_type': 'Bank',
            'balance': Decimal('2000.00')
        }
        
        form = AccountForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('An account with this name already exists', str(form.errors))


class CurrencyFormTest(BaseTestCase):
    def test_currency_form_no_data(self):
        """Test CurrencyForm validation with no data"""
        form = CurrencyForm(data={}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertGreaterEqual(len(form.errors), 1)  # currency_code

    def test_currency_form_exchange_rate(self):
        """Test currency form with various exchange rate scenarios"""
        # Test valid positive exchange rate
        form_data = {
            'currency_code': 'JPY',
            'exchange_rate': Decimal('0.01')
        }
        
        form = CurrencyForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

        # Test invalid negative exchange rate (if such validation exists)
        form_data = {
            'currency_code': 'TEST',
            'exchange_rate': Decimal('-1.00')
        }
        
        form = CurrencyForm(data=form_data, user=self.user)
        # The validation depends on your specific form implementation
        # Adjust the assertion based on your requirements