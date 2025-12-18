# 📱 GOOGLE QR CODE SETUP - QUICK GUIDE

## Your Google Review QR Code

I can see you've uploaded a beautiful Google Review QR code with the text "Check us out on Google" and "Shiv Shakti Electrical" branding.

---

## 🔧 **HOW TO ADD IT TO RECEIPTS:**

### **Option 1: Use Your Uploaded Image** (Recommended)

1. **Find your uploaded image:**
   - Look in: `C:/Users/housh/.gemini/antigravity/brain/031dfae1-c131-4132-bc39-60ceda84e07b/`
   - File: `uploaded_image_1766053619885.png`

2. **Copy the image to:**
   ```
   c:\Users\housh\Desktop\SSElectricals\SSElectricals\media\static\images\google_review_qr.png
   ```

3. **Create the directory if it doesn't exist:**
   ```bash
   cd c:\Users\housh\Desktop\SSElectricals\SSElectricals
   mkdir media\static\images
   ```

4. **Copy the file:**
   - Manually copy the uploaded PNG to the target location
   - Rename it to: `google_review_qr.png`

---

### **Option 2: Update Template Path**

If you want to keep the image elsewhere, update this line in:
**File:** `firstApp/templates/firstApp/admin/receipt_print.html`
**Line:** ~271

Change:
```html
<img src="{% static 'images/google_review_qr.png' %}" alt="Google Reviews">
```

To your actual path:
```html
<img src="/media/your/actual/path/your_qr_image.png" alt="Google Reviews">
```

---

## ✅ **VERIFICATION:**

### **Test the QR Code:**

1. Create a test receipt
2. Go to print view
3. You should see TWO QR codes:
   - **Left:** Receipt details (auto-generated)
   - **Right:** Your Google review QR code

If the Google QR doesn't show:
- Check console for 404 errors
- Verify file path is correct
- Ensure image file exists
- Check file permissions

---

## 🎨 **YOUR QR CODE DESIGN:**

Based on your uploaded image:
- ✅ Google logo at top
- ✅ "Check us out on Google" text
- ✅ Colorful bordered QR code
- ✅ "Shiv Shakti Electrical" branding
- ✅ Professional hexagonal design

This is PERFECT for customer receipts! It will:
- Encourage Google reviews
- Look professional on A4 receipts
- Match your branding

---

## 📋 **QUICK COMMANDS:**

```bash
# Create directory
cd c:\Users\housh\Desktop\SSElectricals\SSElectricals
mkdir media\static\images

# Copy your Google QR image there and name it:
# google_review_qr.png
```

Then it will automatically work on receipts!

---

## 🖨️ **HOW IT APPEARS ON RECEIPTS:**

```
┌─────────────────────────────────────┐
│  QR CODES SECTION                   │
├─────────────┬───────────────────────┤
│ Receipt QR  │  Google Review QR    │
│             │                       │
│   [Auto]    │   [Your Branding]    │
│             │                       │
│ "Scan for   │ "Check us on Google" │
│  receipt    │  "Scan to review!"   │
│  details"   │                       │
└─────────────┴───────────────────────┘
```

Both QR codes will be:
- Side by side
- Same size (150px height)
- Clearly labeled
- Print-friendly

---

**That's it! Your Google QR will appear on every receipt!** 🎉

