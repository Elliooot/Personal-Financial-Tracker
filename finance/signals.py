from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from finance.models import Category

User = get_user_model()

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