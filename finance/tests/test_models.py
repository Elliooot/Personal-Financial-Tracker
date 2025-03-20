from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from decimal import Decimal
import uuid

from finance.models import User, Currency, Account, Category, Transaction, Budget

class UserModelTest(TestCase):
    """Test cases for the User model."""
    
    def test_create_user(self):
        """Test creating a regular user with basic attributes."""
        User = get_user_model()
        username = f'testuser-{uuid.uuid4()}'
        email = f'test-{uuid.uuid4()}@example.com'
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
        
        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser with admin privileges."""
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username=f'admin-{uuid.uuid4()}',
            email=f'admin-{uuid.uuid4()}@example.com',
            password='adminpass123'
        )
        
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class CurrencyModelTest(TestCase):
    """Test cases for the Currency model."""
    
    def setUp(self):
        """Set up test data for the currency tests."""
        self.user = get_user_model().objects.create_user(
            username=f'testuser-{uuid.uuid4()}',
            email=f'test-{uuid.uuid4()}@example.com',
            password='testpass123'
        )
        
        # Generate unique currency codes for testing
        self.system_currency_code = f'SYS{uuid.uuid4().hex[:3]}'
        self.user_currency_code = f'USR{uuid.uuid4().hex[:3]}'
        
        self.system_currency = Currency.objects.create(
            user=None,
            currency_code=self.system_currency_code,
            exchange_rate=Decimal('1.0')
        )
        
        self.user_currency = Currency.objects.create(
            user=self.user,
            currency_code=self.user_currency_code,
            exchange_rate=Decimal('1.12')
        )

    def test_currency_str_representation(self):
        """Test the string representation of Currency objects."""
        expected_system = f'System - {self.system_currency_code}'
        expected_user = f'{self.user.username} - {self.user_currency_code}'
        
        self.assertEqual(str(self.system_currency), expected_system)
        self.assertEqual(str(self.user_currency), expected_user)


class AccountModelTest(TestCase):
    """Test cases for the Account model."""
    
    def setUp(self):
        """Set up test data for the account tests."""
        self.user = get_user_model().objects.create_user(
            username=f'testuser-{uuid.uuid4()}',
            email=f'test-{uuid.uuid4()}@example.com',
            password='testpass123'
        )
        
        self.account = Account.objects.create(
            user=self.user,
            account_name='Test Account',
            account_type='Bank',
            balance=Decimal('1000.00'),
            order=1
        )

    def test_account_str_representation(self):
        """Test the string representation of Account objects."""
        self.assertEqual(str(self.account), 'Test Account')

    def test_account_balance(self):
        """Test account balance storage and retrieval."""
        self.assertEqual(self.account.balance, Decimal('1000.00'))
        
        # Update the balance
        self.account.balance = Decimal('1500.50')
        self.account.save()
        
        # Refresh from database and check balance
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('1500.50'))


class CategoryModelTest(TestCase):
    """Test cases for the Category model."""
    
    def setUp(self):
        """Set up test data for the category tests."""
        self.user = get_user_model().objects.create_user(
            username=f'testuser-{uuid.uuid4()}',
            email=f'test-{uuid.uuid4()}@example.com',
            password='testpass123'
        )
        
        # Use random names to avoid unique constraint issues
        self.income_name = f'Income-{uuid.uuid4()}'
        self.expense_name = f'Expense-{uuid.uuid4()}'
        
        self.income_category = Category.objects.create(
            user=self.user,
            name=self.income_name,
            is_income=True
        )
        
        self.expense_category = Category.objects.create(
            user=self.user,
            name=self.expense_name,
            is_income=False
        )

    def test_category_str_representation(self):
        """Test the string representation of Category objects."""
        self.assertEqual(str(self.income_category), self.income_name)
        self.assertEqual(str(self.expense_category), self.expense_name)

    def test_category_properties(self):
        """Test category properties are correctly stored and retrieved."""
        self.assertTrue(self.income_category.is_income)
        self.assertFalse(self.expense_category.is_income)
        
        # Update is_income flag and verify it persists
        self.expense_category.is_income = True
        self.expense_category.save()
        
        # Refresh from database
        self.expense_category.refresh_from_db()
        self.assertTrue(self.expense_category.is_income)


class TransactionModelTest(TestCase):
    """Test cases for the Transaction model."""
    
    def setUp(self):
        """Set up test data for the transaction tests."""
        self.user = get_user_model().objects.create_user(
            username=f'testuser-{uuid.uuid4()}',
            email=f'test-{uuid.uuid4()}@example.com',
            password='testpass123'
        )
        
        # Currency with unique code
        self.currency_code = f'CUR{uuid.uuid4().hex[:3]}'
        self.currency = Currency.objects.create(
            user=None,
            currency_code=self.currency_code,
            exchange_rate=Decimal('1.0')
        )
        
        self.account = Account.objects.create(
            user=self.user,
            account_name='Test Account',
            account_type='Bank',
            balance=Decimal('1000.00'),
            order=1
        )
        
        self.category_name = f'Category-{uuid.uuid4()}'
        self.category = Category.objects.create(
            user=self.user,
            name=self.category_name,
            is_income=False
        )
        
        self.transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('50.00'),
            category=self.category,
            currency=self.currency,
            date='2024-03-15',
            description='Grocery shopping',
            transaction_type=False,  # Expense
            is_saved=False
        )

    def test_transaction_str_representation(self):
        """Test the string representation of Transaction objects."""
        expected = f'{self.category_name} - 50.00 - 2024-03-15'
        self.assertEqual(str(self.transaction), expected)
    
    def test_transaction_is_saved_flag(self):
        """Test toggling the is_saved flag on transactions."""
        self.assertFalse(self.transaction.is_saved)
        
        # Toggle the flag
        self.transaction.is_saved = True
        self.transaction.save()
        
        # Refresh from database
        self.transaction.refresh_from_db()
        self.assertTrue(self.transaction.is_saved)


class BudgetModelTest(TestCase):
    """Test cases for the Budget model."""
    
    def setUp(self):
        """Set up test data for the budget tests."""
        self.user = get_user_model().objects.create_user(
            username=f'testuser-{uuid.uuid4()}',
            email=f'test-{uuid.uuid4()}@example.com',
            password='testpass123'
        )
        
        self.category_name = f'Category-{uuid.uuid4()}'
        self.category = Category.objects.create(
            user=self.user,
            name=self.category_name,
            is_income=False
        )
        
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            budget_amount=Decimal('300.00'),
            period='2024-03-01'
        )

    def test_budget_str_representation(self):
        """Test the string representation of Budget objects."""
        expected = f'2024-03-01 - {self.category_name} - 300.00'
        self.assertEqual(str(self.budget), expected)
    
    def test_budget_amount_update(self):
        """Test updating budget amounts."""
        self.assertEqual(self.budget.budget_amount, Decimal('300.00'))
        
        # Update budget amount
        self.budget.budget_amount = Decimal('450.00')
        self.budget.save()
        
        # Refresh from database
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.budget_amount, Decimal('450.00'))