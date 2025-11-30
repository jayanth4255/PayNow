from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.views import APIView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.urls import reverse
from django.contrib.auth import logout
import uuid
import pytz
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from .models import BankUser, userprofile
from . import serializers
from .serializers import (
    SetPinSerializer,
    TransferMoneySerializer,
    ReceiverMoneySerializer,
    VarifyPinSerializer,
    BalanceEnquarySerializer,
    Transactions
)
from django.http import JsonResponse
import json

SESSION_TIMEOUT_MINUTES = 1


# --------------------------
# Home / Index View
# --------------------------
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    reward_message = request.session.pop('reward_message', None)
    username = "User"  # default

    phone = request.session.get('login_phone')
    if phone:
        try:
            user = BankUser.objects.get(phone=phone)
            username = user.registered_name or "User"
        except BankUser.DoesNotExist:
            request.session.pop('login_phone', None)
            phone = None

    context = {
        'username': username,
        'reward_message': reward_message
    }
    return render(request, 'index.html', context)


# --------------------------
# Profile View
# --------------------------
def profile_view(request):
    phone = request.session.get('login_phone')
    if not phone:
        return redirect('login')

    try:
        bank_user = BankUser.objects.get(phone=phone)
    except BankUser.DoesNotExist:
        return redirect('login')

    username = f"user_{phone}"
    try:
        auth_user = User.objects.get(username=username)
        user_email = auth_user.email
    except User.DoesNotExist:
        user_email = ''

    first_letter = bank_user.registered_name[0].upper() if bank_user.registered_name else 'U'
    profile_image_url = "/static/images/default_user.png"

    user_upi_id = f"{bank_user.registered_name}{bank_user.bank_account_num[-4:]}@PayNow"

    context = {
        'name': bank_user.registered_name,
        'phone': bank_user.phone,
        'bank_name': bank_user.bank_name,
        'account_number': bank_user.bank_account_num,
        'email': user_email,
        'profile_image_url': profile_image_url,
        'initial': first_letter,
        'upi_id': user_upi_id,
    }
    return render(request, 'profile.html', context)


# --------------------------
# Logout View
# --------------------------
def logout_view(request):
    logout(request)
    for key in ['login_phone', 'phone', 'pin', 'signin_phone']:
        request.session.pop(key, None)
    return redirect('index')


# --------------------------
# Success View
# --------------------------
def success(request):
    return render(request, 'success.html')


# --------------------------
# Scan & Pay API
# --------------------------
class Scan_Pay(APIView):
    def get(self, request):
        return render(request, 'scan_pay.html')

    def post(self, request):
        data = json.loads(request.body)
        pa = data.get("pa")
        pn = data.get("pn")
        am = data.get("am")
        tn = data.get("tn")
        # TODO: Validate or simulate payment
        return JsonResponse({"status": "success", "message": "UPI QR processed"})


# --------------------------
# Login View
# --------------------------
@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='dispatch')
class LoginView(APIView):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        request.session['login_phone'] = phone

        serializer = serializers.LoginSerializer(data={'phone': phone, 'password': password})
        if serializer.is_valid():
            try:
                user = BankUser.objects.get(phone=phone)
                profile, _ = userprofile.objects.get_or_create(phone=phone)

                if not profile.first_login_reward_claimed:
                    user.balance += 50
                    user.save()
                    profile.first_login_reward_claimed = True
                    profile.save()

                    Transactions.objects.create(
                        transaction_id=str(uuid.uuid4()).replace("-", "").upper()[:12],
                        transaction_date=timezone.now(),
                        sender_name="System Reward",
                        sender_phone_number="SYSTEM",
                        sender_bank_name="-",
                        sender_bank_account="-",
                        sender_upi_id="PayNow",
                        transaction_amount=50,
                    )

                    request.session['reward_message'] = "🎉 You earned ₹50 reward for your first login!"

                return redirect('index')
            except BankUser.DoesNotExist:
                return render(request, 'login.html', {'error': 'User does not exist'})
        return render(request, 'login.html', {'error': 'Invalid phone or password'})


# --------------------------
# Transfer Money View
# --------------------------
@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='dispatch')
class TransferMoney(APIView):
    def get(self, request):
        phone = request.session.get('login_phone')
        if not phone:
            return redirect('login')

        receiver = request.GET.get('receiver')
        amount = request.GET.get('amount')

        context = {}
        if receiver:
            try:
                user = BankUser.objects.get(phone=receiver)
                masked_account = 'X' * (len(user.bank_account_num) - 4) + user.bank_account_num[-4:]
                context = {
                    'Receiver_name': user.registered_name,
                    'account_last': masked_account,
                    'bank': user.bank_name,
                    'prefill_amount': amount or ''
                }
                request.session['receiver_phone_number'] = receiver
                request.session['payment_start_time'] = timezone.now().isoformat()
                request.session['context'] = context
                return render(request, 'receiver_page.html', context)
            except BankUser.DoesNotExist:
                return render(request, 'transfer_money.html', {'error': 'Phone number not found.'})

        return render(request, 'transfer_money.html')

    def post(self, request):
        receiver_phone_number = request.POST.get('receiver_phone_number')
        request.session['receiver_phone_number'] = receiver_phone_number
        request.session['payment_start_time'] = timezone.now().isoformat()

        serializer = TransferMoneySerializer(
            data=request.POST,
            context={'receiver_phone': receiver_phone_number}
        )

        if not serializer.is_valid():
            return render(request, 'transfer_money.html', {
                'error': 'Phone number not Linked with Bank Account',
                'show_fav_button': False
            })

        try:
            user = BankUser.objects.get(phone=receiver_phone_number)
            masked_account = 'X' * (len(user.bank_account_num) - 4) + user.bank_account_num[-4:]
            context = {
                'Receiver_name': user.registered_name,
                'account_last': masked_account,
                'bank': user.bank_name,
                'show_fav_button': True
            }
            request.session['context'] = context
            return render(request, 'receiver_page.html', context)
        except BankUser.DoesNotExist:
            return render(request, 'transfer_money.html', {
                'error': 'Phone number not found.',
                'show_fav_button': False
            })


# --------------------------
# Receiver View
# --------------------------
@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='dispatch')
class Receiver(APIView):
    def post(self, request):
        receiver_phone_number = request.session.get('receiver_phone_number')
        amount = request.POST.get('amount')
        request.session['amount'] = amount
        phone = request.session.get('login_phone')
        context = request.session.get('context')

        if not phone or not amount:
            return render(request, 'receiver_page.html', context)

        serializer = ReceiverMoneySerializer(data={
            'receiver_phone_number': receiver_phone_number,
            'amount': amount,
            'phone': phone
        })

        if serializer.is_valid():
            return redirect('enter_pin')

        if receiver_phone_number == phone:
            return render(request, 'transfer_money.html', {**(context or {}), 'error': "You can't transfer money to yourself."})

        return render(request, 'receiver_page.html')


# --------------------------
# Verify PIN View
# --------------------------
@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='dispatch')
class VerifyPin(APIView):
    def get(self, request):
        return render(request, 'enter_pin.html', {
            'form_action_url': reverse('enter_pin')
        })

    def post(self, request):
        sender_phone_number = request.session.get('login_phone')
        amount = request.session.get('amount')
        receiver_phone_number = request.session.get('receiver_phone_number')
        entered_pin = request.POST.get('pin')

        if not sender_phone_number or not amount or not receiver_phone_number:
            return render(request, 'enter_pin.html', {'error': 'Session expired. Please try again.'})

        try:
            sender = BankUser.objects.get(phone=sender_phone_number)
            receiver = BankUser.objects.get(phone=receiver_phone_number)
            pin = userprofile.objects.get(phone=sender_phone_number).pin
        except (BankUser.DoesNotExist, userprofile.DoesNotExist):
            return redirect('login')

        # Build transaction
        sender_account_number = sender.bank_account_num
        receiver_account_number = receiver.bank_account_num
        sender_upi_id = f"{sender.registered_name}{sender.bank_account_num[-4:]}@PayNow"
        receiver_upi_id = f"{receiver.registered_name}{receiver.bank_account_num[-4:]}@PayNow"
        transaction_id = str(uuid.uuid4()).replace("-", "").upper()[:12]

        ist = pytz.timezone("Asia/Kolkata")
        transaction_date = timezone.now().astimezone(ist)

        # Session timeout
        start_time_str = request.session.get('payment_start_time')
        if start_time_str:
            try:
                start_time = timezone.datetime.fromisoformat(start_time_str)
                if (timezone.now() - start_time).total_seconds() > SESSION_TIMEOUT_MINUTES * 60:
                    return render(request, 'index.html', {'error': 'Session expired. Please try again.'})
            except ValueError:
                pass

        serializer = VarifyPinSerializer(data={
            'transaction_id': transaction_id,
            'transaction_date': transaction_date,
            'sender_name': sender.registered_name,
            'sender_phone_number': sender_phone_number,
            'sender_bank_name': sender.bank_name,
            'sender_bank_account': sender_account_number,
            'sender_upi_id': sender_upi_id,
            'transaction_amount': amount,
            'receiver_upi_id': receiver_upi_id,
            'receiver_name': receiver.registered_name,
            'receiver_phone_number': receiver_phone_number,
            'receiver_bank_account': receiver_account_number,
            'receiver_bank_name': receiver.bank_name,
            'pin': pin,
            'entered_pin': entered_pin,
        })

        if serializer.is_valid():
            return render(request, 'success.html', {
                'amount': amount,
                'receiver_phone_number': receiver_phone_number,
                'reference_id': transaction_id,
                'timestamp': transaction_date,
            })

        return render(request, 'enter_pin.html', {'error': 'Invalid PIN'})


class check_phone(APIView):
    def get(self, request):
        return render(request, 'check_phone.html', {'submitted': False})

    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        aadhar = request.POST.get('aadhar', '').strip()
        email = request.POST.get('email', '').strip()
        request.session['signin_phone'] = phone
        request.session['email'] = email

        context = {
            'submitted': True,
            'phone': phone
        }

        if not phone:
            context['error'] = "Phone number is required."
            return render(request, 'check_phone.html', context)

        if userprofile.objects.filter(phone=phone).exists():
            context['existing_error'] = "This phone number is already registered."
            return render(request, 'check_phone.html', context)

        if BankUser.objects.filter(phone=phone).exists() and BankUser.objects.filter(aadhaar=aadhar).exists():
            user = BankUser.objects.get(phone=phone)
            masked_account = 'X' * (len(user.bank_account_num) - 4) + user.bank_account_num[-4:]

            context['Registerd_name'] = user.registered_name
            context['account_last'] = masked_account
            context['bank'] = user.bank_name
            context['user_created'] = True
        else:
            context['error'] = "This phone number or Aadhaar is not linked to any bank account."

        return render(request, 'check_phone.html', context)


class set_upi(APIView):
    def get(self, request):
        return render(request, 'set_upi.html')

    def post(self, request):
        pin = request.POST.get('pin1')
        phone = request.session.get('signin_phone')
        email = request.GET.get('email')
        request.session['pin'] = userprofile.objects.get(phone=phone).pin

        if request.session.get('change_pin_allowed'):
            try:
                user = userprofile.objects.get(phone=phone)
                user.pin = pin
                user.save()
                del request.session['change_pin_allowed']
                return render(request, 'pin_success.html', {'success': True})
            except userprofile.DoesNotExist:
                return render(request, 'set_upi.html', {'error': "User not found."})

        serializer = serializers.SetPinSerializer(data={'pin': pin, 'phone': phone, 'email': email})
        if serializer.is_valid():
            serializer.save()
            return render(request, 'pin_success.html', {'success': True})

        errors = serializer.errors
        phone_error = errors.get('phone')
        error_message = phone_error[0] if phone_error else "Invalid data provided."

        return render(request, 'set_upi.html', {
            'error': error_message,
        })
from django.http import HttpResponse
from django.db import connection
import json
import os

def test_db(request):
    try:
        # Tries to connect to the database
        connection.ensure_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")  # simple query to check DB
        return HttpResponse("✅ Database is connected!")
    except Exception as e:
        return HttpResponse(f"❌ Database connection error: {e}")


def load_data(request):
    """Load BankUser data from JSON file - for free tier Render deployments"""
    from django.conf import settings
    
    json_file = os.path.join(settings.BASE_DIR, 'bankuser_data.json')
    
    if not os.path.exists(json_file):
        return HttpResponse(f"❌ Error: {json_file} not found!")
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        loaded = 0
        skipped = 0
        output = [f"📁 Loading {len(data)} BankUser records...<br><br>"]
        
        for item in data:
            fields = item['fields']
            phone = fields.get('phone')
            
            # Check if user already exists
            if BankUser.objects.filter(phone=phone).exists():
                output.append(f"⏭️  Skipped {phone} (already exists)<br>")
                skipped += 1
                continue
            
            # Create the BankUser
            BankUser.objects.create(
                registered_name=fields.get('registered_name'),
                phone=fields.get('phone'),
                password=fields.get('password'),
                bank_name=fields.get('bank_name'),
                bank_account_num=fields.get('bank_account_num'),
                ifsc_code=fields.get('ifsc_code'),
                balance=fields.get('balance', 0),
                aadhaar=fields.get('aadhaar'),
                upi_id=fields.get('upi_id'),
            )
            loaded += 1
            output.append(f"✅ Loaded: {fields.get('registered_name')} ({phone})<br>")
        
        output.append(f"<br><strong>🎉 Done! Loaded {loaded} users, skipped {skipped}</strong><br>")
        output.append(f"📊 Total BankUsers in database: {BankUser.objects.count()}")
        
        return HttpResponse(''.join(output))
    
    except Exception as e:
        return HttpResponse(f"❌ Error loading data: {str(e)}")


class ChangeUpiPin(APIView):
    def get(self, request):
        return render(request, 'change_upi.html')

    def post(self, request):
        aadhar = request.POST.get('aadhar')
        old_pin = request.POST.get('old_pin')
        phone = request.session.get('login_phone')

        try:
            user_pin = userprofile.objects.get(phone=phone)
            user_aadhar = BankUser.objects.get(phone=phone)
        except userprofile.DoesNotExist:
            messages.error(request, "Invalid Aadhaar or phone number.")
            return render(request, 'change_upi.html')

        if user_pin.pin != old_pin:
            messages.error(request, "Incorrect old UPI PIN.")
            return render(request, 'change_upi.html')
        if user_aadhar.aadhaar != aadhar:
            messages.error(request, "Aadhaar is not Matched")
            return render(request, 'change_upi.html')

        request.session['change_pin_allowed'] = True
        return redirect('set_upi')


class balance_enquary(APIView):
    def get(self, request):
        if not request.session.get('login_phone'):
            return redirect('login')
        return render(request, 'enter_pin.html', {
            'form_action_url': reverse('balance')  # This is already used in template
        })

    def post(self, request):
        if not request.session.get('login_phone'):
            return redirect('login')

        pin = request.POST.get('pin')
        phone = request.session.get('login_phone')

        if not pin or not phone:
            return render(request, 'enter_pin.html', {
                'error': 'Missing PIN or session expired.',
                'form_action_url': reverse('balance')
            })

        serializer = serializers.BalanceEnquarySerializer(data={'pin': pin, 'phone': phone})

        if serializer.is_valid():
            user = BankUser.objects.get(phone=phone)
            balance = user.balance
            bank_account_num = user.bank_account_num
            bank_name = user.bank_name

            return render(request, 'balance_enquary.html', {
                'balance': balance,
                'account_number': bank_account_num,
                'bank_name': bank_name
            })

        return render(request, 'enter_pin.html', {
            'error': 'Invalid PIN.',
            'form_action_url': reverse('balance')
        })



def transaction_history(request):
    phone = request.session.get('login_phone')
    if not phone:
        return redirect('login')

    transactions = Transactions.objects.filter(
        Q(sender_phone_number=phone) | Q(receiver_phone_number=phone)
    ).order_by('-transaction_date')

    return render(request, 'transaction_history.html', {
        'transactions': transactions,
        'logged_in_phone': phone
    })


