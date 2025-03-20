from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import uuid
from datetime import date, timedelta

from finance.models import Currency, Account, Category, Transaction, Budget

class StatisticsViewTest(TestCase):
    """Test suite for statistics view functionality."""
    
    def setUp(self):
        """Set up the test environment for statistics tests."""
        # Define URLs
        self.statistics_url = reverse('statistics')
        self.transaction_dates_url = reverse('transaction_dates')
        self.statistics_data_url = reverse('statistics_data')
        
        # Create test user with random username to avoid conflicts
        username = f'testuser-{uuid.uuid4()}'
        email = f'{username}@example.com'
        
        self.user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
        
        # Create test data
        self.currency, _ = Currency.objects.get_or_create(
            user=None,
            currency_code='GBP',
            defaults={'exchange_rate': Decimal('1.0')}
        )
        
        self.account = Account.objects.create(
            user=self.user,
            account_name=f'Account-{uuid.uuid4()}',
            account_type='Bank',
            balance=Decimal('1000.00'),
            order=1
        )
        
        # Create categories with unique names
        self.expense_category = Category.objects.create(
            user=self.user,
            name=f'Expense-{uuid.uuid4()}',
            is_income=False
        )
        
        self.income_category = Category.objects.create(
            user=self.user,
            name=f'Income-{uuid.uuid4()}',
            is_income=True
        )
        
        # Define test dates - use a previous month and current month
        today = date.today()
        current_month = today.replace(day=15)
        previous_month = (today.replace(day=1) - timedelta(days=1)).replace(day=15)
        
        # Create transactions for previous month
        self.prev_expense = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('50.00'),
            category=self.expense_category,
            currency=self.currency,
            date=previous_month,
            description=f'Previous Month Expense-{uuid.uuid4()}',
            transaction_type=False,  # Expense
            is_saved=False
        )
        
        self.prev_income = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('2000.00'),
            category=self.income_category,
            currency=self.currency,
            date=previous_month,
            description=f'Previous Month Income-{uuid.uuid4()}',
            transaction_type=True,  # Income
            is_saved=False
        )
        
        # Create transactions for current month
        self.curr_expense = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('60.00'),
            category=self.expense_category,
            currency=self.currency,
            date=current_month,
            description=f'Current Month Expense-{uuid.uuid4()}',
            transaction_type=False,  # Expense
            is_saved=False
        )
        
        self.curr_income = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('2100.00'),
            category=self.income_category,
            currency=self.currency,
            date=current_month,
            description=f'Current Month Income-{uuid.uuid4()}',
            transaction_type=True,  # Income
            is_saved=False
        )
        
        # Create a budget for the current month
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.expense_category,
            budget_amount=Decimal('300.00'),
            period=date(today.year, today.month, 1)
        )
    
    def test_statistics_view_GET_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(self.statistics_url)
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertTrue('login' in response.url)
    
    def test_statistics_view_GET_authenticated(self):
        """Test that authenticated users can access the statistics page."""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(self.statistics_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'statistics.html')
    
    def test_transaction_dates_api(self):
        """Test the transaction dates API endpoint returns proper data."""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(self.transaction_dates_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Parse the response data
        data = json.loads(response.content)
        
        # Verify the structure of the response
        self.assertIn('years', data)
        self.assertIn('monthsByYear', data)
        
        # Verify that we have at least the current year
        current_year = date.today().year
        self.assertIn(current_year, data['years'])
    
    def test_statistics_data_year_mode(self):
        """Test statistics data API in year mode."""
        self.client.login(username=self.user.username, password='testpass123')
        
        current_year = date.today().year
        url = f"{self.statistics_data_url}?year={current_year}&mode=year"
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Parse the response data
        data = json.loads(response.content)
        
        # Check that expected fields are present
        self.assertIn('income', data)
        self.assertIn('expense', data)
        self.assertIn('balance', data)
        self.assertIn('monthly_data', data)
        self.assertIn('expense_by_category', data)
        self.assertIn('income_by_category', data)
        
        # Verify that monthly data contains entries
        self.assertTrue(len(data['monthly_data']) > 0)
        
        # Verify that our expense and income categories are represented
        self.assertIn(self.expense_category.name, data['expense_by_category'])
        self.assertIn(self.income_category.name, data['income_by_category'])
    
    def test_statistics_data_month_mode(self):
        """Test statistics data API in month mode."""
        self.client.login(username=self.user.username, password='testpass123')
        
        today = date.today()
        url = f"{self.statistics_data_url}?year={today.year}&month={today.month}&mode=month"
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Parse the response data
        data = json.loads(response.content)
        
        # Check for month-specific data structure
        self.assertIn('daily_data', data)
        
        # Verify income, expense, and balance calculations
        # Total income should match our current month transaction
        self.assertAlmostEqual(float(data['income']), float(self.curr_income.amount), places=2)
        # Total expense should match our current month transaction
        self.assertAlmostEqual(float(data['expense']), float(self.curr_expense.amount), places=2)
        # Balance should be income - expense
        expected_balance = float(self.curr_income.amount) - float(self.curr_expense.amount)
        self.assertAlmostEqual(float(data['balance']), expected_balance, places=2)