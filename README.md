# ⚡ Shiv Shakti Electricals - E-Commerce & Service Management Platform

[![Django](https://img.shields.io/badge/Django-5.2.8-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

A comprehensive, full-featured e-commerce and service management platform built for **Shiv Shakti Electricals**, an electrical shop based in Indore, Madhya Pradesh, India. This platform handles online product sales, appointment booking for electrical services, warranty management, and complete administrative operations.

---

## 🌟 Key Features

### 🛒 E-Commerce Module
- **Product Catalog** with categories, brands, and multiple images
- **Smart Search & Filters** (by category, price, stock status)
- **Product Visibility Control** - Admin can show/hide products on website
- **Trending Products** section on homepage
- **Shopping Cart** with quantity management
- **Wishlist** functionality for logged-in users
- **Product Reviews & Ratings** (verified purchase reviews only)

### 📦 Order Management
- **Enquiry-Based Purchase Flow** - Customers submit enquiries, admin shares pricing, customer confirms
- **Price Quote System** - Admin sets prices, customers approve before order confirmation
- **Order Types**: Online Delivery or Pick from Store
- **Dynamic Delivery Pricing** based on distance (Google Maps Distance Matrix API)
- **Free Delivery** for first-time customers within 2 KM
- **Delivery OTP Verification** - Secure delivery confirmation
- **Order Status Tracking** with email notifications
- **Order Cancellation** with reason tracking

### 📅 Appointment Booking System
- **Service Types** with configurable pricing
- **Google Places Autocomplete** for address entry
- **Distance-Based Service Charges**
- **Electrician Assignment** by admin
- **Appointment Status Workflow**: Pending → Confirmed → In Progress → Completed
- **Automated Email Notifications** to customers and electricians
- **Review Request** after service completion

### 👨‍🔧 Electrician Management (NEW)
- **Electrician Profiles** with photo, experience, specializations
- **Home Page Visibility Toggle** - Show featured electricians on homepage
- **Active/Inactive Status** management
- **Assignment to Appointments**

### 🛡️ Warranty Management (NEW)
- **Product Warranty Registration** by admin
- **Auto-Calculated Expiry Dates** (months or years)
- **Warranty Status**: Active, Expired, Voided
- **Customer Warranty Dashboard** - Users can view their warranties
- **Email Notifications** on warranty registration
- **Warranty Search & Filters** in admin panel

### 👤 User Management
- **Email OTP Authentication** (passwordless login)
- **User Profiles** with address, phone, profile picture
- **Theme Preference** (Light/Dark mode)
- **Order History** with review capability
- **My Receipts** - View offline purchase receipts
- **My Warranties** - View registered product warranties
- **Account Deletion** with password confirmation

### 📊 Admin Dashboard
- **Analytics Dashboard** with sales, orders, appointment statistics
- **Daily Sales Entry** with auto-calculation (Cash + Online)
- **Daily Expenses Tracking**
- **Product Management** with search, filters, visibility toggle
- **Order Management** with status updates and pricing
- **Appointment Management** with electrician assignment
- **User Management** - View user details, orders, cart, wishlist
- **Review Moderation** - Approve/reject product reviews
- **Notifications & Announcements** system
- **Activity Logs** - Track all admin actions
- **Offline Receipts** - Generate receipts for walk-in customers

### 📧 Professional Email System
- **HTML Email Templates** with responsive design
- **Email Types**:
  - Appointment Confirmation
  - Electrician Assignment
  - Appointment Completed + Review Request
  - Order Status Updates
  - Out for Delivery with OTP
  - Order Delivered + Review Request
  - Warranty Registered
  - Price Quote Confirmation
- **Email Logging** with retry mechanism
- **Async Email Sending** for non-blocking operations

---

## 🔧 Technology Stack

| Category | Technology |
|----------|------------|
| **Backend** | Django 5.2.8 (Python) |
| **Database** | MySQL / PostgreSQL / SQLite |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5 |
| **Maps & Location** | Google Maps API, Google Places API, Distance Matrix API |
| **Email** | Django Email with HTML templates |
| **PDF Generation** | ReportLab |
| **Image Processing** | Pillow |
| **Distance Calculation** | GeoPy, Google Distance Matrix |
| **Task Queue** | Threading (async emails) |
| **File Storage** | Local storage (configurable for S3) |

---

## 📁 Project Structure

```
SSElectricals/
├── SSElectricals/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── firstApp/               # Main application
│   ├── models.py           # Database models
│   ├── views.py            # User-facing views
│   ├── admin_views.py      # Admin panel views
│   ├── urls.py             # URL routing
│   ├── forms.py            # Django forms
│   ├── email_utils.py      # Email utilities
│   ├── utils.py            # Helper functions
│   ├── decorators.py       # Custom decorators
│   ├── templates/          # HTML templates
│   │   ├── firstApp/       # User templates
│   │   ├── admin/          # Admin templates
│   │   └── emails/         # Email templates
│   ├── static/             # Static files (CSS, JS, images)
│   └── migrations/         # Database migrations
├── static/                 # Collected static files
├── media/                  # User uploaded files
├── manage.py
├── requirements.txt
└── .env                    # Environment variables
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- MySQL / PostgreSQL (or SQLite for development)
- Google Cloud API credentials (for Maps services)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/SSElectricals.git
cd SSElectricals/SSElectricals
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=mysql://user:password@localhost/sselectricals

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Shiv Shakti Electricals <your-email@gmail.com>

# Google APIs
GOOGLE_PLACES_API_KEY=your-places-api-key
GOOGLE_SERVER_API_KEY=your-server-api-key

# Site URL
SITE_URL=http://127.0.0.1:8000
```

### Step 5: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 7: Collect Static Files
```bash
python manage.py collectstatic
```

### Step 8: Run Development Server
```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000`

---

## 📱 Key URLs

| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/products/` | Product catalog |
| `/cart/` | Shopping cart |
| `/checkout/` | Checkout page |
| `/orders/` | Order history |
| `/book-appointment/` | Book electrical service |
| `/my-appointments/` | View appointments |
| `/my-warranties/` | View warranties |
| `/profile/` | User profile |
| `/shop-admin/` | Admin dashboard |
| `/shop-admin/products/` | Product management |
| `/shop-admin/orders/` | Order management |
| `/shop-admin/appointments/` | Appointment management |
| `/shop-admin/electricians/` | Electrician management |
| `/shop-admin/warranties/` | Warranty management |

---

## 🎨 Screenshots

### Home Page
- Hero section with featured products
- Category showcase
- Trending products grid
- Featured electricians section

### Admin Dashboard
- Sales analytics charts
- Quick action cards
- Recent orders/appointments
- Activity logs

### Product Management
- Search, filter, sort functionality
- Visibility toggle
- Stock status indicators
- Quick edit/delete actions

---

## 🔐 Security Features

- **CSRF Protection** on all forms
- **Email OTP Authentication** (no password storage for customers)
- **Admin Staff Verification** decorators
- **Secure Password Hashing** (Argon2)
- **Session Management**
- **Input Validation** on all forms
- **SQL Injection Protection** via Django ORM
- **XSS Protection** via template auto-escaping
- **Delivery OTP** for order verification

---

## 📈 Future Enhancements

- [ ] Mobile app (Flutter/React Native)
- [ ] Payment gateway integration (Razorpay/PayU)
- [ ] SMS notifications (Twilio integration ready)
- [ ] Inventory management with barcode scanning
- [ ] Multi-vendor support
- [ ] Customer loyalty program
- [ ] Advanced reporting & exports
- [ ] WhatsApp Business API integration

---

## 🤝 Contributing

This is a private project for Shiv Shakti Electricals. For any inquiries or support, please contact the development team.

---

## 📞 Contact

**Shiv Shakti Electricals**
- 📍 Indore, Madhya Pradesh, India
- 📞 +91-9993149226
- 📧 shivshaktielectrical1430@gmail.com
- 🌐 [Google Business Profile](https://g.page/r/Cep_YI3hg2KCEBM)

---

## 📄 License

This project is proprietary software owned by Shiv Shakti Electricals. All rights reserved.

---

<div align="center">
  <p>Built with ❤️ for <strong>Shiv Shakti Electricals</strong></p>
  <p>© 2024 Shiv Shakti Electricals. All rights reserved.</p>
</div>
