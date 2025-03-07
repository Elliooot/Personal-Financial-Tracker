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
            { 'date': '2024/02/01', 'category': 'Transportation', 'transaction_type': 'Expenditure', 'currency': '£', 'amount': '2.95', 'description': 'First Glasgow' },
            { 'date': '2024/02/01', 'category': 'Investment',     'transaction_type': 'Income',      'currency': '£', 'amount': '4000', 'description': 'CHRIS LIU' },
            { 'date': '2024/02/03', 'category': 'Food',           'transaction_type': 'Expenditure', 'currency': '£', 'amount': '7.45', 'description': 'Subway' },
            { 'date': '2024/02/03', 'category': 'Shopping',       'transaction_type': 'Expenditure', 'currency': '£', 'amount': '4.90', 'description': 'Circuit top up' },
            { 'date': '2024/02/16', 'category': 'Food',           'transaction_type': 'Expenditure', 'currency': '£', 'amount': '7.45', 'description': 'Subway' },
            { 'date': '2024/02/20', 'category': 'Food',           'transaction_type': 'Expenditure', 'currency': '£', 'amount': '7.45', 'description': 'Subway' }
        ]

        # Get default objects: Please ensure these objects exist or create them as needed.
        default_user = User.objects.first()
        default_account = Account.objects.first()
        default_currency = Currency.objects.first()

        if not default_user or not default_account or not default_currency:
            self.stdout.write(self.style.ERROR("Default user, account or currency not found."))
            return

        for data in transactions:
            date_obj = datetime.strptime(data['date'], '%Y/%m/%d').date()
            transaction_type = True if data['transaction_type'] == 'Income' else False
            cleaned_amount = Decimal(data['amount'].replace('£', ''))
            
            cat_obj, created = Category.objects.get_or_create(name=data['category'])
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {data['category']}"))

            Transaction.objects.create(
                user=default_user,
                account=default_account,
                currency=default_currency,
                date=date_obj,
                category=cat_obj,
                amount=Decimal(data['amount']),
                description=data['description'],
                transaction_type=transaction_type,
                saved_transaction=False
            )
            self.stdout.write(self.style.SUCCESS(f"Inserted transaction: {data['description']}"))

        self.stdout.write(self.style.SUCCESS("All transactions have been populated."))
