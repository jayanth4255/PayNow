from django.contrib.auth.models import User
from django.db import models




class BankUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    registered_name = models.CharField(max_length=200)
    age = models.IntegerField()
    city = models.CharField(max_length=100)
    location = models.TextField()
    phone = models.CharField(max_length=20,unique=True)
    bank_account_num = models.CharField(max_length=30,unique=True)
    bank_name = models.CharField(max_length=100)
    ifsc = models.CharField(max_length=20)
    bank_location = models.CharField(max_length=100)
    aadhaar = models.CharField(max_length=20,unique=True)
    pan = models.CharField(max_length=20,unique=True)
    bank_id = models.CharField(max_length=100)
    balance = models.BigIntegerField()
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class userprofile(models.Model):
    phone=models.CharField(unique=True)
    pin  = models.CharField(max_length=6,null=True,blank=True)
    first_login_reward_claimed = models.BooleanField(default=False)
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    def __str__(self):
        return self.phone
    
class Transactions(models.Model):
    transaction_id = models.CharField(max_length=20, unique=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True, null=True)
    sender_name = models.CharField(max_length=100, null=True)
    sender_phone_number = models.CharField(max_length=50, null=True)
    sender_bank_name = models.CharField(max_length=100, null=True)
    sender_bank_account = models.CharField(max_length=30, null=True, blank=True)
    sender_upi_id = models.CharField(max_length=100, null=True)
    sender_bank_id = models.CharField(max_length=100, null=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    receiver_bank_ID = models.CharField(max_length=100, null=True)
    receiver_name = models.CharField(max_length=100, null=True)
    receiver_phone_number = models.CharField(null=True)
    receiver_bank_account = models.CharField(max_length=30, null=True)
    receiver_upi_id = models.CharField(max_length=100, null=True)
    receiver_bank_name = models.CharField(max_length=100, null=True)
    transaction_type = models.CharField(max_length=20, null=True)
    def __str__(self):
        return self.sender_name
    
    

    
    


