# Quick script to update FY format in models.py
import re

# Read the file
with open('firstApp/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace OfflineReceipt FY method - line 912
content = content.replace(
    'return f"{today.year}-{str(today.year + 1)[2:]}"',
    'return str(today.year + 1)[2:]  # Just ending year: \'25\''
)

# Replace OfflineReceipt FY method - line 914
content = content.replace(
    'return f"{today.year - 1}-{str(today.year)[2:]}"',
    'return str(today.year)[2:]  # Just current year: \'25\''
)

# Replace Order FY method - similar pattern
content = content.replace(
    'return f"{today.year}-{str(today.year + 1)[2:]}"',
    'return str(today.year + 1)[2:]  # Just ending year'
, 1)  # Only first occurrence already done

# Find and replace in Order model too
order_pattern1 = r'(\s+if today\.month >= 4:.*?)\n(\s+return f"\{today\.year\}-\{str\(today\.year \+ 1\)\[2:\]\}")'
order_replace1 = r'\1\n\2'  # Will handle separately

# Write back
with open('firstApp/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Updated FY format in models.py")
