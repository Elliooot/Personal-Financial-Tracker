from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
class Currency(models.Model):
    currency_code = models.CharField(max_length=10, unique=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2)

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=15, decimal_places=2)

class Category(models.Model):
    name = models.CharField(max_length=255)

class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('shopping', 'Shopping'),
        ('transportation', 'Transportation'),
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('housing', 'Housing'),
        ('medical', 'Medical'),
        ('investment', 'Investment'),
        ('others', 'Others'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    transaction_type = models.BooleanField(default=True)  # True for income, False for expense
    is_recurring = models.BooleanField(default=False)
    saved_transaction = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.category} - {self.amount}"

    
class RecurringTransaction(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    recurring_period = models.CharField(max_length=50)

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2)
    period = models.DateField()

class Reminder(models.Model):
    recurring_transaction = models.ForeignKey(RecurringTransaction, on_delete=models.CASCADE)
    due_date = models.DateField()
    status = models.BooleanField(default=False)
