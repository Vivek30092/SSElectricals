"""
Data Migration Script: Consolidate Duplicate Daily Expenditure Entries

This script merges duplicate expense entries (Online + Cash for same date)
into single combined entries before applying the model migration.

Run this BEFORE running 'python manage.py migrate'
"""

# Run this in Django shell: python manage.py shell

from firstApp.models import DailyExpenditure
from decimal import Decimal
from collections import defaultdict

print("=" * 60)
print("DAILY EXPENDITURE CONSOLIDATION SCRIPT")
print("=" * 60)

# Group expenses by date
expenses_by_date = defaultdict(list)
all_expenses = DailyExpenditure.objects.all().order_by('date', 'payment_method')

for expense in all_expenses:
    expenses_by_date[expense.date].append(expense)

print(f"\nTotal unique dates: {len(expenses_by_date)}")

# Find dates with duplicates
duplicates_found = []
for date, expenses in expenses_by_date.items():
    if len(expenses) > 1:
        duplicates_found.append((date, expenses))

print(f"Dates with duplicate entries: {len(duplicates_found)}")

if not duplicates_found:
    print("\n✅ No duplicates found! Safe to run migration.")
else:
    print("\n⚠️  Duplicates found. Details:\n")
    
    for date, expenses in duplicates_found:
        print(f"Date: {date}")
        online_amount = Decimal('0.00')
        cash_amount = Decimal('0.00')
        descriptions = []
        admin_user = None
        
        for exp in expenses:
            print(f"  - {exp.payment_method}: ₹{exp.amount} ({exp.description[:50]}...)")
            
            if exp.payment_method == 'Online':
                online_amount = exp.amount
            elif exp.payment_method == 'Cash':
                cash_amount = exp.amount
            
            descriptions.append(f"{exp.payment_method}: {exp.description}")
            if not admin_user:
                admin_user = exp.admin
        
        total = online_amount + cash_amount
        combined_description = " | ".join(descriptions)
        
        print(f"  → Will merge to: Online: ₹{online_amount}, Cash: ₹{cash_amount}, Total: ₹{total}")
        print()

    # Ask for confirmation
    response = input("\n🔄 Do you want to consolidate these entries now? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🔄 Consolidating entries...")
        
        consolidated_count = 0
        for date, expenses in duplicates_found:
            online_amount = Decimal('0.00')
            cash_amount = Decimal('0.00')
            descriptions = []
            admin_user = None
            created_at = None
            
            # Collect data from all entries
            for exp in expenses:
                if exp.payment_method == 'Online':
                    online_amount = exp.amount
                elif exp.payment_method == 'Cash':
                    cash_amount = exp.amount
                
                descriptions.append(f"{exp.payment_method}: {exp.description}")
                
                if not admin_user:
                    admin_user = exp.admin
                if not created_at or exp.created_at < created_at:
                    created_at = exp.created_at
            
            combined_description = " | ".join(descriptions)
            
            # Delete old entries
            for exp in expenses:
                exp.delete()
            
            # Create new consolidated entry
            # Note: We can't use the new fields yet (migration not applied)
            # So we create a temporary entry with old structure
            # After migration, this will need the new structure
            
            # For now, create ONE entry with combined amount
            DailyExpenditure.objects.create(
                date=date,
                amount=online_amount + cash_amount,
                payment_method='Cash',  # Temporary - will be removed after migration
                description=combined_description,
                admin=admin_user
            )
            
            consolidated_count += 1
            print(f"✅ Consolidated {date}: Online ₹{online_amount} + Cash ₹{cash_amount} = Total ₹{online_amount + cash_amount}")
        
        print(f"\n✅ Successfully consolidated {consolidated_count} dates!")
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("1. Now you need to manually update these consolidated entries")
        print("2. After migration, edit each entry to split into online_amount and cash_amount")
        print("3. Or export the data, delete all, migrate, then re-import with new structure")
        
    else:
        print("\n❌ Consolidation cancelled.")
        print("\n📝 Alternative approaches:")
        print("1. Export your expense data to CSV")
        print("2. Delete all expense  entries: DailyExpenditure.objects.all().delete()")
        print("3. Run migration: python manage.py migrate")
        print("4. Re-import data in new format (with online_amount and cash_amount columns)")

print("\n" + "=" * 60)
