# 🚀 PHASE 3: ADVANCED RECEIPT FEATURES

## ✅ **PHASE 2 COMPLETE:**
- Receipt creation form ✅
- A4 print template ✅
- Receipt management ✅
- Void/correction workflows ✅
- Google QR code integrated ✅

---

## 🎯 **PHASE 3 OBJECTIVES:**

### **1. Online Order Receipt Integration** 🛒
Apply FY-based receipt numbering to online orders

### **2. User Dashboard - My Receipts** 👤
Let customers view their linked receipts

### **3. PDF Generation** 📄
Actual PDF download (not just print)

### **4. Receipt Email Automation** 📧
Auto-send receipts to customer email

---

## 📋 **IMPLEMENTATION PLAN:**

### **Step 1: Online Order Receipt Numbering**

#### **A. Update Order Model**
Add FY-based receipt fields to Order model:
```python
# In firstApp/models.py - Order model

# Add these fields:
receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
financial_year = models.CharField(max_length=10, blank=True, null=True)
receipt_sequence = models.IntegerField(blank=True, null=True)
receipt_qr_code = models.ImageField(upload_to='order_qrcodes/', blank=True, null=True)
receipt_generated_at = models.DateTimeField(blank=True, null=True)

# Add method:
def generate_receipt_number(self):
    """Generate FY-based receipt number for order"""
    if not self.receipt_number:
        from datetime import date
        today = date.today()
        if today.month >= 4:
            fy = f"{today.year}-{str(today.year + 1)[2:]}"
        else:
            fy = f"{today.year - 1}-{str(today.year)[2:]}"
        
        # Get last order receipt in this FY
        last_order = Order.objects.filter(
            financial_year=fy
        ).exclude(receipt_number__isnull=True).order_by('-receipt_sequence').first()
        
        seq = (last_order.receipt_sequence + 1) if last_order else 1
        
        self.financial_year = fy
        self.receipt_sequence = seq
        self.receipt_number = f"ORD/{fy}/{seq:04d}"  # Different prefix for orders
        self.receipt_generated_at = timezone.now()
        self.save()
```

#### **B. Generate Receipt on Order Confirmation**
```python
# In views.py - when order is confirmed/completed

def admin_update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        
        # Generate receipt when order is confirmed/completed
        if new_status in ['Confirmed', 'Completed'] and not order.receipt_number:
            order.generate_receipt_number()
            order.generate_receipt_qr_code()  # Similar to offline receipts
        
        order.save()
        return redirect('admin_order_detail', order_id=order.id)
```

#### **C. Order Receipt Print Template**
Create `admin/order_receipt_print.html`:
- Same layout as offline receipts
- Shows order items
- Includes both QR codes
- Status: Confirmed/Completed/Delivered

---

### **Step 2: User Dashboard - My Receipts**

#### **A. View for User Receipts**
```python
# In views.py

@login_required
def my_receipts(request):
    """Show user's offline receipts and order receipts"""
    user = request.user
    
    # Offline receipts linked by email
    offline_receipts = OfflineReceipt.objects.filter(
        buyer_email=user.email,
        status='ACTIVE'
    ).order_by('-created_at')
    
    # Order receipts
    order_receipts = Order.objects.filter(
        user=user,
        receipt_number__isnull=False
    ).order_by('-created_at')
    
    return render(request, 'firstApp/my_receipts.html', {
        'offline_receipts': offline_receipts,
        'order_receipts': order_receipts
    })
```

#### **B. Template**
Create `my_receipts.html`:
- Tab interface: "Shop Receipts" | "Order Receipts"
- List with receipt number, date, amount
- View/Download/Print buttons
- Filter by date range

---

### **Step 3: PDF Generation**

#### **A. Install WeasyPrint** (Already done ✅)

#### **B. PDF Generation Function**
```python
# In utils.py or views.py

from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import FileResponse
import io

def generate_receipt_pdf(receipt):
    """Generate PDF for offline receipt"""
    # Render template to HTML string
    html_string = render_to_string('admin/admin_receipt_print.html', {
        'receipt': receipt,
        'items': receipt.items.all()
    })
    
    # Generate PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_file = html.write_pdf()
    
    # Save to model
    from django.core.files.base import ContentFile
    receipt.pdf_file.save(
        f'receipt_{receipt.receipt_number.replace("/", "_")}.pdf',
        ContentFile(pdf_file),
        save=True
    )
    
    return pdf_file

# Update receipt_pdf view:
@staff_member_required
def receipt_pdf(request, receipt_id):
    """Download PDF of receipt"""
    receipt = get_object_or_404(OfflineReceipt, id=receipt_id)
    
    # Generate or retrieve PDF
    if not receipt.pdf_file:
        pdf_data = generate_receipt_pdf(receipt)
    else:
        with receipt.pdf_file.open('rb') as pdf:
            pdf_data = pdf.read()
    
    # Return as file download
    response = FileResponse(
        io.BytesIO(pdf_data),
        content_type='application/pdf',
        as_attachment=True,
        filename=f'Receipt_{receipt.receipt_number.replace("/", "_")}.pdf'
    )
    return response
```

---

### **Step 4: Email Automation**

#### **A. Email Receipt Function**
```python
# In utils.py

def send_receipt_email(receipt, recipient_email=None):
    """Send receipt via email"""
    if not recipient_email:
        recipient_email = receipt.buyer_email
    
    if not recipient_email:
        return False
    
    subject = f'Receipt {receipt.receipt_number} - {receipt.shop_name}'
    
    # Generate PDF
    pdf_data = generate_receipt_pdf(receipt)
    
    # Email body
    html_message = render_to_string('emails/receipt_email.html', {
        'receipt': receipt,
        'customer_name': receipt.buyer_name
    })
    
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email]
    )
    
    email.attach_alternative(html_message, "text/html")
    
    # Attach PDF
    email.attach(
        f'Receipt_{receipt.receipt_number.replace("/", "_")}.pdf',
        pdf_data,
        'application/pdf'
    )
    
    email.send()
    return True
```

#### **B. Auto-send on Receipt Creation**
```python
# In create_receipt view - after saving receipt:

if receipt.buyer_email:
    try:
        send_receipt_email(receipt)
        messages.success(request, f'Receipt emailed to {receipt.buyer_email}')
    except:
        messages.warning(request, 'Receipt created but email failed')
```

---

## 📊 **PRIORITY ORDER:**

1. **High Priority:**
   - ✅ Online order receipt numbering
   - ✅ User dashboard "My Receipts"

2. **Medium Priority:**
   - PDF generation
   - Email automation

3. **Low Priority (Future):**
   - Advanced filters
   - Export to Excel
   - Multiple templates

---

## 🚀 **NEXT ACTION:**

Would you like me to:

**A)** Start with Online Order Receipt Integration?
**B)** Start with User Dashboard "My Receipts"?
**C)** Start with PDF Generation?
**D)** Do all three in sequence?

Let me know and I'll implement your choice! 🎯

