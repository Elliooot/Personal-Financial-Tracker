from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from finance.models import Category, Currency
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
            "Rent",
            "Utilities",
            "Food",
            "Transportation",
            "Entertainment",
            "Health",
            "Insurance",
            "Education",
            "Gift",
            "Other Expense"
        ]
        
        # create income categories
        for category_name in default_income_categories:
            Category.objects.create(
                user=instance,
                name=category_name,
                is_income=True
            )
        
        # create expense categories
        for category_name in default_expense_categories:
            Category.objects.create(
                user=instance,
                name=category_name,
                is_income=False
            )

@receiver(post_save, sender=User)
def create_default_currencies(sender, instance, created, **kwargs):
    """
    When a new user is created, add default currencies to their account.
    This signal handler will be called automatically after a User is saved.
    """
    if created:  # Only proceed if this is a new user being created
        # Default currencies to add for each new user
        default_currencies = ['GBP', 'EUR', 'USD']
        
        for currency_code in default_currencies:
            try:
                # Try to get the exchange rate from the API
                try:
                    exchange_rate = get_exchange_rate_with_gbp_base(currency_code)
                    logger.info(f"Got exchange rate for {currency_code}: {exchange_rate}")
                except Exception as e:
                    # If API fails, use fallback values
                    logger.warning(f"Failed to get exchange rate for {currency_code}: {str(e)}")
                    if currency_code == 'GBP':
                        exchange_rate = 1.0  # GBP to GBP is always 1.0
                    elif currency_code == 'EUR':
                        exchange_rate = 1.19  # Example fallback
                    elif currency_code == 'USD':
                        exchange_rate = 1.28  # Example fallback
                    else:
                        exchange_rate = 1.0  # Default fallback
                
                # Create the currency for this user
                Currency.objects.create(
                    user=instance,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate
                )
                logger.info(f"Created default currency {currency_code} for user {instance.username}")
                
            except Exception as e:
                logger.error(f"Error creating default currency {currency_code} for {instance.username}: {str(e)}")