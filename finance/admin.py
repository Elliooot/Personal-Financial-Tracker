from django.contrib import admin
from .models import User, Currency, Account, Category, Transaction

admin.site.register(User)
admin.site.register(Currency)
admin.site.register(Account)
admin.site.register(Category)
admin.site.register(Transaction)
