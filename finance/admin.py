from django.contrib import admin
from finance.models import User, Currency, Account, Category, Transaction, RecurringTransaction, Budget, Reminder

admin.site.register(User)
admin.site.register(Currency)
admin.site.register(Account)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(RecurringTransaction)
admin.site.register(Budget)
admin.site.register(Reminder)