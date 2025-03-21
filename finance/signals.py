from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from finance.models import Category, Currency, Account
import logging
from finance.currency_utils import get_exchange_rate_with_gbp_base

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:  # only create default categories for new users
        # income categories
        default_income_categories = [
            "Salary",
            "Bonus",
            "Investment Income",
            "Gift",
            "Other Income"
        ]
        
        # expense categories
        default_expense_categories = [
            "Food",
            "Housing",
            "Clothing",
            "Utilities",
            "Transportation",
            "Entertainment",
            "Health",
            "Other Expenses"
        ]

        existing_categories = Category.objects.filter(
            user=instance
        )
        
        # create income categories
        for category_name in default_income_categories:
            if not existing_categories.filter(name=category_name, is_income=True).exists():
                Category.objects.create(
                    user=instance,
                    name=category_name,
                    is_income=True
                )
        
        # create expense categories
        for category_name in default_expense_categories:
            if not existing_categories.filter(name=category_name, is_income=False).exists():
                Category.objects.create(
                    user=instance,
                    name=category_name,
                    is_income=False
                )

@receiver(post_save, sender=User)
def create_default_currencies(sender, instance, created, **kwargs):
    if created:
        default_currencies = [
            {'code': 'GBP', 'rate': 1.0},
            {'code': 'EUR', 'rate': 1.12},
            {'code': 'USD', 'rate': 1.29}
        ]

        for currency_data in default_currencies:
            try:
                currency_code = currency_data['code']
                exchange_rate = currency_data['rate']
                
                currency, created_currency = Currency.objects.get_or_create(
                    user=None,
                    currency_code=currency_code,
                    defaults={'exchange_rate': exchange_rate}
                )
                
                if not created_currency and currency.exchange_rate != exchange_rate:
                    currency.exchange_rate = exchange_rate
                    currency.save()
                    
            except Exception as e:
                logger.error(f"Error ensuring default currency {currency_code}: {str(e)}")

@receiver(post_save, sender=User)
def create_default_account(sender, instance, created, **kwargs):
    """
    Create a default Cash account with a balance of 100 for new users.
    """
    if created:  # only create default account for new users
        try:
            # Create a Cash account with initial balance of 100
            Account.objects.create(
                user=instance,
                account_name="Cash",
                account_type="Cash",
                balance=100.00,
                order=0  # Make it the first account in order
            )
            logger.info(f"Created default Cash account for user {instance.username}")
        except Exception as e:
            logger.error(f"Error creating default Cash account for user {instance.username}: {str(e)}")