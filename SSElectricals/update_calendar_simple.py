# Simple script to change to calendar year (Jan-Dec)
import re

with open('firstApp/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: OfflineReceipt method (multiline)
old_pattern1 = r'(@staticmethod\s+def get_current_financial_year\(\):\s+""".*?"""\s+from datetime import date\s+today = date\.today\(\)\s+if today\.month >= 4:.*?return.*?\n\s+else:.*?return.*?\n)'

new_code1 = '''@staticmethod
    def get_current_financial_year():
        """Get current calendar year (last 2 digits) - Jan to Dec"""
        from datetime import date
        return str(date.today().year)[2:]  # Returns '25' for 2025, '26' for 2026
'''

# Replace both occurrences (OfflineReceipt and Order)
content = re.sub(old_pattern1, new_code1, content, flags=re.DOTALL)

# Simpler approach - direct string replacement
content = content.replace(
    '''if today.month >= 4:  # April onwards
            return f"{today.year}-{str(today.year + 1)[2:]}"
        else:  # January to March
            return f"{today.year - 1}-{str(today.year)[2:]}"''',
    '''return str(today.year)[2:]  # Returns '25' for 2025, '26' for 2026'''
)

# Also try without f-string (in case it was already updated)
content = content.replace(
    '''if today.month >= 4:  # April onwards
            return str(today.year + 1)[2:]  # Just ending year
        else:  # January to March
            return str(today.year)[2:]  # Just current year''',
    '''return str(today.year)[2:]  # Returns '25' for 2025, '26' for 2026'''
)

# Write back
with open('firstApp/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[SUCCESS] Updated to calendar year format!")
print("Logic: January 1 to December 31 = Same year")
print("Example: 2025 = '25', 2026 = '26'")
