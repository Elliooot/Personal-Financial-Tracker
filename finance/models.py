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

    def __str__(self) -> str:
        return self.username
    
class Currency(models.Model):
    currency_code = models.CharField(max_length=10, unique=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return self.currency_code

class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('Cash', 'Cash'), 
        ('Bank', 'Bank'), 
        ('Credit Card', 'Credit Card'), 
        ('Debit Card', 'Debit Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self) -> str:
        return self.account_name

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_income = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    transaction_type = models.BooleanField(default=True)  # True for income, False for expense
    is_saved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category} - {self.amount} - {self.date}"
        return f"{self.category} - {self.amount} - {self.date}"

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2)
    period = models.DateField()

    def __str__(self):
        return f"{self.period} - {self.category} - {self.budget_amount}"