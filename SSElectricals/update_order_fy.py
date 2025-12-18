# Update Order model FY format
with open('firstApp/models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Update line 219 (Order model - April onwards)
updated = 0
for i, line in enumerate(lines):
    if i == 218:  # Line 219 (0-indexed)
        if 'return f"{today.year}-{str(today.year + 1)[2:]}"' in line:
            lines[i] = '            return str(today.year + 1)[2:]  # Just ending year\n'
            print(f"[OK] Updated line {i+1}: Order FY (April onwards)")
            updated += 1
    elif i == 220:  # Line 221
        if 'return f"{today.year - 1}-{str(today.year)[2:]}"' in line:
            lines[i] = '            return str(today.year)[2:]  # Just current year\n'
            print(f"[OK] Updated line {i+1}: Order FY (Jan-March)")
            updated += 1

# Write back
with open('firstApp/models.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

if updated > 0:
    print(f"\n[SUCCESS] Order model FY format updated! ({updated} lines changed)")
    print("Receipt format now: ORD/25/0001")
else:
    print("\n[INFO] No changes needed - already updated!")
