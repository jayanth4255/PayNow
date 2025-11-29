from django.contrib import admin
from .models import BankUser,userprofile,Transactions
admin.site.register(BankUser)
admin.site.register(userprofile)
admin.site.register(Transactions)

# Register your models here.
