import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "personal_finance_tracker.settings")
django.setup()

from django.core.management.base import BaseCommand
from finance.models import Category, Transaction, User, Account, Currency
from datetime import datetime
from decimal import Decimal

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        transactions = [
            { 'date': '2024/02/01', 'category': 'transportation', 'amount': '-£2.95', 'description': 'First Glasgow' },
            { 'date': '2024/02/01', 'category': 'investment', 'amount': '+£4000', 'description': 'CHRIS LIU' },
            { 'date': '2024/02/03', 'category': 'food', 'amount': '-£7.45', 'description': 'Subway' },
            { 'date': '2024/02/03', 'category': 'shopping', 'amount': '-£4.90', 'description': 'Circuit top up' },
            { 'date': '2024/02/16', 'category': 'food', 'amount': '-£7.45', 'description': 'Subway' },
            { 'date': '2024/02/20', 'category': 'food', 'amount': '-£7.45', 'description': 'Subway' }
        ]
        categories = [
            "Food",
            "Shopping",
            "Transportation",
            "Education",
            "Entertainment",
            "Housing",
            "Medical",
            "Investment",
            "Others",
        ]

        # Get default objects: Please make sure these objects exist in the database, or create them as needed
        default_user = User.objects.first()
        default_account = Account.objects.first()
        default_currency = Currency.objects.first()

        if not default_user or not default_account or not default_currency:
            self.stdout.write(self.style.ERROR("Default user, account or currency not found."))
            return

        for data in transactions:
            date_obj = datetime.strptime(data['date'], '%Y/%m/%d').date()
            amount_str = data['amount']
            # Determine income or expenditure
            transaction_type = True if amount_str.startswith('+') else False
            # Remove +, - and currency symbols
            cleaned_amount = Decimal(amount_str.replace('£','').replace('+','').replace('-',''))
            
            created = Transaction.objects.create(
                user=default_user,
                account=default_account,
                currency=default_currency,
                date=date_obj,
                category=data['category'],
                amount=cleaned_amount,
                description=data['description'],
                transaction_type=transaction_type,
                is_recurring=False,
                saved_transaction=False
            )
            if created:
                self.stdout.write(self.style.NOTICE(f"Transaction {data['description']} already exists"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Inserted transaction: {data['description']}"))

        # Insert categories
        # for cat in categories:
        #     obj, created = Category.objects.get_or_create(name=cat)
        #     if created:
        #         self.stdout.write(self.style.SUCCESS(f"Inserted category: {cat}"))
        #     else:
        #         self.stdout.write(self.style.NOTICE(f"Category {cat} already exists"))

        self.stdout.write(self.style.SUCCESS("All transactions have been populated."))
