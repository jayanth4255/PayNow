#!/usr/bin/env python
"""
Standalone script to load BankUser data into the database.
Run this on Render after deployment to populate the BankUser table.

Usage: python load_bankusers.py
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PAYMENT.settings')
django.setup()

from APIS.models import BankUser

def load_bankusers():
    """Load BankUser data from JSON file"""
    
    json_file = 'bankuser_data.json'
    
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found!")
        print(f"   Please ensure {json_file} exists in the project root.")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"📁 Loading {len(data)} BankUser records...")
    
    loaded = 0
    skipped = 0
    
    for item in data:
        fields = item['fields']
        phone = fields.get('phone')
        
        # Check if user already exists
        if BankUser.objects.filter(phone=phone).exists():
            print(f"⏭️  Skipping {phone} (already exists)")
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
        print(f"✅ Loaded: {fields.get('registered_name')} ({phone})")
    
    print(f"\n🎉 Done! Loaded {loaded} users, skipped {skipped}")
    print(f"📊 Total BankUsers in database: {BankUser.objects.count()}")

if __name__ == '__main__':
    load_bankusers()
