# Update to Calendar Year format (Jan-Dec instead of April-March)
with open('firstApp/models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and update OfflineReceipt.get_current_financial_year method
updated = 0
for i, line in enumerate(lines):
    # OfflineReceipt model - around line 910-913
    if i >= 905 and i <= 915:
        if 'def get_current_financial_year():' in line:
            # Found the method, update next few lines
            # Replace the entire logic with simple calendar year
            lines[i+1] = '        """Get current calendar year (last 2 digits)"""\n'
            lines[i+2] = '        from datetime import date\n'
            lines[i+3] = '        return str(date.today().year)[2:]  # Just last 2 digits of current year\n'
            # Remove the old if-else logic
            if i+4 < len(lines) and 'today = date.today()' in lines[i+4]:
                lines[i+4] = ''  # Remove old line
            if i+5 < len(lines) and 'if today.month' in lines[i+5]:
                lines[i+5] = ''  # Remove old line
            if i+6 < len(lines) and 'return str(today.year' in lines[i+6]:
                lines[i+6] = ''  # Remove old line  
            if i+7 < len(lines) and 'else:' in lines[i+7]:
                lines[i+7] = ''  # Remove old line
            if i+8 < len(lines) and 'return str(today.year' in lines[i+8]:
                lines[i+8] = ''  # Remove old line
            updated += 1
            print(f"[OK] Updated OfflineReceipt calendar year method")
            break

# Find and update Order.get_current_financial_year method  
for i, line in enumerate(lines):
    # Order model - around line 215-220
    if i >= 210 and i <= 225:
        if 'def get_current_financial_year():' in line and updated == 1:
            # Found Order method
            lines[i+1] = '        """Get current calendar year (last 2 digits)"""\n'
            lines[i+2] = '        from datetime import date\n'
            lines[i+3] = '        return str(date.today().year)[2:]  # Just last 2 digits of current year\n'
            # Remove old if-else logic
            if i+4 < len(lines) and 'today = date.today()' in lines[i+4]:
                lines[i+4] = ''
            if i+5 < len(lines) and 'if today.month' in lines[i+5]:
                lines[i+5] = ''
            if i+6 < len(lines) and 'return str(today.year' in lines[i+6]:
                lines[i+6] = ''
            if i+7 < len(lines) and 'else:' in lines[i+7]:
                lines[i+7] = ''
            if i+8 < len(lines) and 'return str(today.year' in lines[i+8]:
                lines[i+8] = ''
            updated += 1
            print(f"[OK] Updated Order calendar year method")
            break

# Write back
with open('firstApp/models.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

if updated >= 2:
    print(f"\n[SUCCESS] Calendar year format applied to both models!")
    print("Now using: Jan 1 - Dec 31 = Same year number")
    print("Example: All of 2025 = 25, All of 2026 = 26")
elif updated == 1:
    print("\n[PARTIAL] Updated OfflineReceipt only")
else:
    print("\n[ERROR] Could not find methods to update")
