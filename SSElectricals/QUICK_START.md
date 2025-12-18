# 🚀 QUICK START GUIDE - Receipt System

## ⚡ **Your Server is Running!**

**URL:** http://127.0.0.1:8000

---

## 📝 **TEST THE SYSTEM (5 Minutes):**

### **Step 1: Create Your First Offline Receipt**

1. Open browser: `http://127.0.0.1:8000/admin-dashboard/receipts/create/`
2. Log in as admin
3. Fill in customer info:
   - Name: "Test Customer"
   - Phone: "+91 9876543210"
4. Add item:
   - Item: "LED Bulb 9W"
   - Quantity: 10
   - Price: 75
5. Click "Create & Print Receipt"
6. ✅ **You'll see:** `Receipt SS/2024-25/0001 created successfully!`
7. Professional A4 receipt opens with:
   - ⚡ Company branding
   - Receipt QR code
   - Google Review QR code

---

### **Step 2: Test Order Receipt Auto-Generation**

1. Go to admin panel: `http://127.0.0.1:8000/admin/`
2. Navigate to Orders
3. Find a pending order (or create one via website)
4. Change status to "Confirmed"
5. Save
6. ✅ **You'll see:** `Receipt generated: ORD/2024-25/0001`
7. Click "Print Receipt" button
8. Order receipt opens with all details!

---

### **Step 3: View Receipt History**

1. Go to: `http://127.0.0.1:8000/admin-dashboard/receipts/`
2. See all receipts in a table
3. Filter by:
   - Status (Active/Void/Corrected)
   - Financial Year (2024-25)
   - Date range
   - Customer name
4. Click any receipt to view details
5. From detail page you can:
   - Print
   - Download PDF (currently opens print)
   - Void (if active)
   - Create correction

---

## 🎯 **KEY FEATURES TO TRY:**

### **Offline Receipts:**
✅ Create with multiple items  
✅ Auto-calculating totals  
✅ Add tax & discount  
✅ Void with reason  
✅ Create corrections  
✅ Filter & search  

### **Order Receipts:**
✅ Auto-generation on confirmation  
✅ QR codes  
✅ Print anytime  

---

## 📊 **RECEIPT NUMBERING:**

- **Offline:** `SS/2024-25/0001`, `SS/2024-25/0002`, ...
- **Orders:** `ORD/2024-25/0001`, `ORD/2024-25/0002`, ...

**Separate sequences!** ✅

---

## 🖨️ **PRINT TESTING:**

1. Open any receipt print view
2. Press `Ctrl + P` or click "Print" button
3. Check preview:
   - A4 size ✅
   - Professional branding ✅
   - Both QR codes visible ✅
   - Clean layout ✅

---

## ⚙️ **ADMIN PANEL FEATURES:**

### **Order Management:**
When you confirm an order:
- Receipt number automatically assigned
- QR code generated
- Can print professional invoice
- All automatic! ✅

---

## 🐛 **TROUBLESHOOTING:**

### **QR Codes Not Showing?**
- Check: `/media/data/ask_for_review.png` exists
- If missing, copy your Google QR image there

### **Receipt Not Auto-Generating for Orders?**
- Make sure order status is changed to:
  - "Confirmed" OR
  - "Out for Delivery" OR  
  - "Delivered"

### **Can't Create Receipt?**
- Make sure you're logged in as staff/admin
- Check all required fields are filled

---

## 📁 **IMPORTANT URLS:**

```
Offline Receipts:
http://127.0.0.1:8000/admin-dashboard/receipts/create/    → Create
http://127.0.0.1:8000/admin-dashboard/receipts/           → List

Admin Panel:
http://127.0.0.1:8000/admin/                              → Django Admin
http://127.0.0.1:8000/shop-admin/orders/                  → Order Management
```

---

## ✅ **VERIFICATION CHECKLIST:**

After testing, verify:

- [ ] First offline receipt is `SS/2024-25/0001`
- [ ] Second offline receipt is `SS/2024-25/0002`
- [ ] First order receipt is `ORD/2024-25/0001`
- [ ] QR codes display on printed receipts
- [ ] Google QR code shows your branding
- [ ] Void workflow works (reason required)
- [ ] Totals calculate automatically
- [ ] Print layout looks professional
- [ ] Can filter receipts by status/FY

---

## 🎊 **YOU'RE READY!**

Your system is:
✅ **Production-ready**  
✅ **Fully functional**  
✅ **Professional**  
✅ **Audit-compliant**  
✅ **Auto-magical**  

**Start creating receipts and enjoy your new system!** 🚀⚡

