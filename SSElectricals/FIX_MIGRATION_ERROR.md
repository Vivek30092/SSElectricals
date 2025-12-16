# Migration Blocker: Duplicate Expense Entries

## ❌ Problem

Migration failing with error:
```
IntegrityError: could not create unique index "unique_daily_expenditure_date"
DETAIL: Key (date)=(2025-12-16) is duplicated.
```

**Cause:** Existing data has multiple expense entries for the same date (Online + Cash separately), but new model requires only ONE entry per date.

---

## ✅ Solution Options

### **Option 1: Fresh Start (Recommended if few expense records)**

**Steps:**
```bash
python manage.py shell
```

```python
from firstApp.models import DailyExpenditure

# Export first (optional - for backup)
expenses = DailyExpenditure.objects.all().values()
import json
with open('expense_backup.json', 'w') as f:
    json.dump(list(expenses), f, default=str)

# Delete all expenses
DailyExpenditure.objects.all().delete()
print("All expenses deleted")
exit()
```

Then:
```bash
python manage.py migrate
```

**Pros:** Clean, simple, guaranteed to work  
**Cons:** Loses existing expense data

---

### **Option 2: Manual Consolidation (Recommended)**

**Steps:**

1. **Identify duplicates:**
```bash
python manage.py shell
```

```python
from firstApp.models import DailyExpenditure
from collections import defaultdict

expenses_by_date = defaultdict(list)
for exp in DailyExpenditure.objects.all():
    expenses_by_date[exp.date].append(exp)

# Show duplicates
for date, exps in expenses_by_date.items():
    if len(exps) > 1:
        print(f"\n{date}:")
        for e in exps:
            print(f"  {e.payment_method}: ₹{e.amount} - {e.description}")
```

2. **For each duplicate date, keep ONE entry, delete rest:**
```python
# Example for 2025-12-16
date_to_fix = '2025-12-16'
expenses = DailyExpenditure.objects.filter(date=date_to_fix)

# Show them
for e in expenses:
    print(f"ID {e.id}: {e.payment_method} ₹{e.amount}")

# Delete one (keep the other)
expense_to_delete_id = 123  # Use actual ID
DailyExpenditure.objects.get(id=expense_to_delete_id).delete()
```

3. **Repeat for all duplicate dates, then:**
```bash
exit()
python manage.py migrate
```

4. **After migration, update the kept entries:**
```bash
python manage.py shell
```

```python
from firstApp.models import DailyExpenditure

# For each date, split the amounts
expense = DailyExpenditure.objects.get(date='2025-12-16')
expense.online_amount = 5000  # Set actual online amount
expense.cash_amount = 3000     # Set actual cash amount
expense.save()  # Total auto-calculates
```

**Pros:** Preserves data  
**Cons:** Manual work required

---

### **Option 3: Automated Script (Semi-Manual)**

**Run the consolidation script:**

```bash
python manage.py shell < consolidate_expenses.py
```

This will:
1. Show all duplicate entries
2. Ask for confirmation
3. Merge duplicates automatically
4. You then run migration

**Note:** You'll still need to manually update entries after migration to split amounts.

---

## 🎯 Recommended Approach

**If you have few expense records (< 20):**
→ Use **Option 1** (Fresh Start)

**If you have important expense data:**
→ Use **Option 2** (Manual Consolidation)

---

## 📋 Step-by-Step (Option 1 - Fresh Start)

```bash
# 1. Backup (optional)
python manage.py shell
```

```python
from firstApp.models import DailyExpenditure
import json

expenses = list(DailyExpenditure.objects.all().values())
with open('expense_backup.json', 'w') as f:
    json.dump(expenses, f, default=str, indent=2)
    
print(f"Backed up {len(expenses)} expenses to expense_backup.json")

# 2. Delete all
DailyExpenditure.objects.all().delete()
print("All expenses deleted - ready for migration")
exit()
```

```bash
# 3. Run migration
python manage.py migrate

# 4. Start server and test
python manage.py runserver
```

---

## 📋 Step-by-Step (Option 2 - Manual)

```bash
# 1. Find duplicates
python manage.py shell
```

```python
from firstApp.models import DailyExpenditure
from collections import defaultdict

by_date = defaultdict(list)
for e in DailyExpenditure.objects.all():
    by_date[e.date].append(e)

duplicates = {d: exps for d, exps in by_date.items() if len(exps) > 1}

print(f"Found {len(duplicates)} dates with duplicates:\n")
for date, exps in duplicates.items():
    print(f"{date}: {len(exps)} entries")
    for e in exps:
        print(f"  ID {e.id}: {e.payment_method} ₹{e.amount}")
    print()
```

```python
# 2. For each duplicate, delete extras
# Example:
DailyExpenditure.objects.get(id=123).delete()  # Replace 123 with actual ID

# Verify no duplicates remain
by_date = defaultdict(list)
for e in DailyExpenditure.objects.all():
    by_date[e.date].append(e)
    
duplicates = {d: exps for d, exps in by_date.items() if len(exps) > 1}
print(f"Remaining duplicates: {len(duplicates)}")

exit()
```

```bash
# 3. Run migration
python manage.py migrate
```

---

## ⚠️ Important Notes

1. **Backup first** if data is important
2. **After migration**, the model structure changes:
   - Old: `amount`, `payment_method`
   - New: `online_amount`, `cash_amount`, `total`
   
3. **Kept entries** will need updating after migration to split into online/cash

---

## 🆘 Quick Fix (Nuclear Option)

If you just want to get past this quickly:

```bash
python manage.py shell
```

```python
from firstApp.models import DailyExpenditure
DailyExpenditure.objects.all().delete()
exit()
```

```bash
python manage.py migrate
```

Done! (But expense data lost)

---

## 📞 Need Help?

If stuck, share:
1. How many expense records you have
2. Whether the data is critical
3. Which option you want to try

---

*Migration Block Status: Waiting for duplicate resolution*
