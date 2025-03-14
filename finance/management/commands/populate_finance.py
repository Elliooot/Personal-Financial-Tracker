import os
import django
from datetime import datetime
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "personal_finance_tracker.settings")
django.setup()

from django.core.management.base import BaseCommand
from finance.models import Transaction, User, Account, Currency, Category

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        transactions = [
            { 'date': '2024/02/01', 'category': 'Transportation', 'transaction_type': 'Expense', 'currency': 'GBP', 'amount': '2.95', 'account': 'Bank', 'description': 'First Glasgow'},
            { 'date': '2024/02/01', 'category': 'Investment',     'transaction_type': 'Income',  'currency': 'GBP', 'amount': '4000', 'account': 'Bank', 'description': 'CHRIS LIU'},
            { 'date': '2024/02/03', 'category': 'Food',           'transaction_type': 'Expense', 'currency': 'GBP', 'amount': '7.45', 'account': 'Cash', 'description': 'Subway'},
            { 'date': '2024/02/03', 'category': 'Shopping',       'transaction_type': 'Expense', 'currency': 'GBP', 'amount': '4.90', 'account': 'Card', 'description': 'Circuit top up'},
            { 'date': '2024/02/16', 'category': 'Food',           'transaction_type': 'Expense', 'currency': 'GBP', 'amount': '7.45', 'account': 'Cash', 'description': 'Subway'},
            { 'date': '2024/02/20', 'category': 'Food',           'transaction_type': 'Expense', 'currency': 'GBP', 'amount': '7.45', 'account': 'Bank', 'description': 'Subway'},
        ]

        # Ensure these default objects exist or create them as needed.
        default_user = User.objects.first()
        default_currency = Currency.objects.first()

        if not default_user or not default_currency:
            print("Default user or currency not found.")
            exit()

        for data in transactions:
            date_obj = datetime.strptime(data['date'], '%Y/%m/%d').date()
            transaction_type = data['transaction_type'] == 'Income'
            amount_decimal = Decimal(data['amount'])

            cat_obj, _ = Category.objects.get_or_create(name=data['category'])
            currency_obj, _ = Currency.objects.get_or_create(currency_code=data['currency'], defaults={'exchange_rate': Decimal('1.00')})
            account_obj, _ = Account.objects.get_or_create(
                user=default_user,
                account_name=data['account'],
                defaults={'balance': Decimal('0.00')}
            )


            Transaction.objects.create(
                user=default_user,
                account=account_obj,
                currency=currency_obj,
                date=date_obj,
                category=cat_obj,
                amount=amount_decimal,
                description=data['description'],
                transaction_type=transaction_type,
                is_saved=False
            )
            print(f"Inserted transaction: {data['description']}")

        print("All transactions have been populated.")