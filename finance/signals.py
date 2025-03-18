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
    When a new user is created, ensure they have access to default currencies.
    """
    if created:
        default_currencies = ['GBP', 'EUR', 'USD']
        for currency_code in default_currencies:
            try:
                system_currency = Currency.objects.filter(
                    currency_code=currency_code
                ).first()
                
                if system_currency:
                    logger.info(f"System currency {currency_code} already exists.")
                else:
                    try:
                        exchange_rate = get_exchange_rate_with_gbp_base(currency_code)
                        logger.info(f"Got exchange rate for {currency_code}: {exchange_rate}")
                    except Exception as e:
                        logger.warning(f"Failed to get exchange rate for {currency_code}: {str(e)}")
                        if currency_code == 'GBP':
                            exchange_rate = 1.0
                        elif currency_code == 'EUR':
                            exchange_rate = 1.19
                        elif currency_code == 'USD':
                            exchange_rate = 1.28
                        else:
                            exchange_rate = 1.0
                    
                    Currency.objects.create(
                        user=None,
                        currency_code=currency_code,
                        exchange_rate=exchange_rate
                    )
                    logger.info(f"Created system default currency {currency_code}.")
            except Exception as e:
                logger.error(f"Error processing default currency {currency_code}: {str(e)}")