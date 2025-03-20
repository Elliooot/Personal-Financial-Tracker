from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

from finance.models import Category, Account, Currency
from finance.forms import CategoryForm

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