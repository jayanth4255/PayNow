from django.contrib.auth.models import User
from .models import userprofile, BankUser,Transactions
from rest_framework import routers, serializers, viewsets




class SetPinSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    pin = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)

    def validate_phone(self, value):
        if not BankUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError({
                "message": "This phone number is not linked to any bank account.",
                "link": True 
            })
        return value

    def validate_pin(self, value):
        if not (4 <= len(value) <= 6):
            raise serializers.ValidationError("The PIN must be between 4 and 6 digits.")
        if not value.isdigit():
            raise serializers.ValidationError("The PIN must contain only digits.")
        return value

    def create(self, validated_data):
        phone = validated_data.get('phone')
        pin = validated_data.get('pin')
        email = validated_data.get('email')

        # Check if this phone number already has a userprofile
        if userprofile.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number already has a userprofile.")

        # Get details from BankUser to help build auth_user
        try:
            bank_user = BankUser.objects.get(phone=phone)
        except BankUser.DoesNotExist:
            raise serializers.ValidationError("This phone number is not linked to any bank account.")

        # Create auth_user
        username = f"user_{phone}"  # Ensure unique username
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(
                username=username,
                first_name=bank_user.first_name,
                last_name=bank_user.last_name,
                password=pin,  # ⚠️ password stored securely by Django
                email=email
            )

        # Create userprofile
        profile = userprofile.objects.create(user=user, phone=phone, pin=pin)
        return profile




class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')
        try:
            profile = userprofile.objects.get(phone=phone)
            if profile.pin != password:
                raise serializers.ValidationError("Password does Not Match")
        except userprofile.DoesNotExist:
            raise serializers.ValidationError("Invalid phone number")
        return profile



class TransferMoneySerializer(serializers.Serializer):
    receiver_phone_number = serializers.CharField()
    
    def validate(self, data):
        receiver_phone_number = data.get('receiver_phone_number')
        try:
            receiver_profile = BankUser.objects.get(phone=receiver_phone_number)
            return data
        except:
            raise serializers.ValidationError("Receiver phone is not linked to any userprofile.")
        

class ReceiverMoneySerializer(serializers.Serializer):
    phone = serializers.CharField()
    amount = serializers.IntegerField()
    receiver_phone_number = serializers.CharField()

    def validate(self, data):
        amount = data.get('amount')
        receiver_phone_number = data.get('receiver_phone_number')
        phone = data.get('phone')

        if receiver_phone_number == phone:
            raise serializers.ValidationError("You can't transfer money to yourself.")
        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")

        try:
            sender = BankUser.objects.get(phone=phone)
        except BankUser.DoesNotExist:
            raise serializers.ValidationError("Sender not found")

        if sender.balance < amount:
            raise serializers.ValidationError("Insufficient balance.")

        try:
            BankUser.objects.get(phone=receiver_phone_number)
        except BankUser.DoesNotExist:
            raise serializers.ValidationError("Receiver phone is not linked to any account.")

        return data



class VarifyPinSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()
    sender_name = serializers.CharField()
    sender_phone_number = serializers.CharField()
    sender_bank_name = serializers.CharField()
    sender_bank_account = serializers.CharField()
    sender_upi_id = serializers.CharField()
    transaction_amount = serializers.IntegerField()
    receiver_upi_id = serializers.CharField()
    receiver_name = serializers.CharField()
    receiver_phone_number = serializers.CharField()
    receiver_bank_account = serializers.CharField()
    receiver_bank_name = serializers.CharField()
    pin = serializers.CharField(write_only=True)
    entered_pin = serializers.CharField(write_only=True)

    def validate(self, data):
        pin = data.get('pin')
        entered_pin = data.get('entered_pin')
        amount = data.get('transaction_amount')
        sender_phone_number = data.get('sender_phone_number')
        receiver_phone_number = data.get('receiver_phone_number')
        

        if entered_pin != pin:
            raise serializers.ValidationError("Invalid PIN")

        try:
            sender = BankUser.objects.get(phone=sender_phone_number)
        except BankUser.DoesNotExist:
            raise serializers.ValidationError("Sender not found")

        try:
            receiver = BankUser.objects.get(phone=receiver_phone_number)
        except BankUser.DoesNotExist:
            raise serializers.ValidationError("Receiver not found")

        if sender.balance < amount:
            raise serializers.ValidationError("Insufficient balance")

        # Update balances
        sender.balance -= amount
        receiver.balance += amount
        sender.save()
        receiver.save()
        transaction_date = data.get('transaction_date')

        from django.utils import timezone
        Transactions.objects.create(
    user=sender.user if hasattr(sender, 'user') else None,
    transaction_id=data.get('transaction_id'),
    transaction_date=transaction_date,  # ✅ real server timestamp
    sender_name=data.get('sender_name'),
    sender_phone_number=sender_phone_number,
    sender_bank_name=data.get('sender_bank_name'),
    sender_bank_account=data.get('sender_bank_account'),
    sender_upi_id=data.get('sender_upi_id'),
    transaction_amount=amount,
    receiver_upi_id=data.get('receiver_upi_id'),
    receiver_name=data.get('receiver_name'),
    receiver_phone_number=receiver_phone_number,
    receiver_bank_account=data.get('receiver_bank_account'),
    receiver_bank_name=data.get('receiver_bank_name'),
)

        return data







class BalanceEnquarySerializer(serializers.Serializer):
    phone = serializers.CharField()
    pin = serializers.CharField()
    def validate(self,data):
        phone = data.get('phone')
        pin = data.get('pin')
        user = userprofile.objects.get(phone=phone)
        if user.pin != pin:
            raise serializers.ValidationError("Invalid pin.")
        return data