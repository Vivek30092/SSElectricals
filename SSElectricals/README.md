# SSElectricals - Advanced Django E-Commerce Platform

A full-featured Django e-commerce platform for electrical products with advanced admin session management, AJAX functionality, smart validations, and a custom admin dashboard.

## 🚀 New Advanced Features

### 1. Admin Session Management
- **Signal-Based Session Tracking**: Django signals automatically track admin login/logout sessions
- **Auto-Logout**: Automatic logout after 30 minutes of inactivity
- **Session Dashboard**: View active admin sessions in real-time
- **Manual Termination**: Superusers can manually terminate other admin sessions
- **Comprehensive Activity Logging**: Automatic CRUD operation logging for:
  - Products (create, update, delete)
  - Categories (create, update, delete)
  - Orders (create, status changes)
  - Login/Logout events with IP tracking

### 2. Dynamic & Responsive Design  
- **Fully Responsive**: Mobile-first design that works on all devices
- **AJAX Cart Operations**: Add/update cart items without page reload
- **Live Search Suggestions**: Dynamic product search with keyboard navigation (arrow keys, enter)
- **Animated UI**: Smooth transitions, hover effects, and loading states
- **Custom CSS**: Professional styling with animations and accessibility features
- **Toast Notifications**: Real-time feedback for user actions

### 3. Smart Validations
- **Frontend Validation**: Real-time form validation with visual feedback
- **Backend Validation**: Server-side validation for security
- **Phone Number**: 10-digit Indian mobile number format
- **Strong Password**: Min 8 chars, uppercase, number, symbol required
- **UPI ID Validation**: Format validation for UPI payments (e.g., username@paytm)
- **Stock Validation**: Prevent orders exceeding available stock
- **No COD Limits**: Unlimited COD orders allowed (removed order restrictions)

### 4. Custom Admin Dashboard
- **Metrics Cards**: Total products, orders, revenue, active sessions
- **Sales Charts**: Daily/weekly/monthly sales visualization with Chart.js 4.0
- **Recent Orders**: Quick view of latest 10 orders
- **Active Sessions**: Monitor logged-in admins with last activity time
- **Activity Log**: Filterable and paginated admin activity history
- **Real-Time Clock**: Server time display
- **Session Auto-Refresh**: Active sessions refresh every 60 seconds

## 📋 Features

### Core E-Commerce
- User authentication (phone number as username)
- Product catalog with categories
- Shopping cart functionality
- Checkout with multiple payment methods
- Order history tracking
- Delivery: Indore only (₹50 delivery charge)

### Admin Features
- Custom user model with profile management
- Product & category management
- Order status tracking
- Session monitoring
- Activity logging
- Custom dashboard

## 🛠 Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Steps

1. **Clone/Navigate to project directory**
```bash
cd "c:\Users\housh\Desktop\SS Electricals\SSElectricals"
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run migrations**
```bash
python manage.py makemigrations firstApp
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
# Use phone number (10 digits) as username
```

6. **Collect static files**
```bash
python manage.py collectstatic
```

7. **Run development server**
```bash
python manage.py runserver
```

8. **Access the application**
- Main site: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/
- Admin dashboard: http://127.0.0.1:8000/admin/dashboard/
- Activity log: http://127.0.0.1:8000/admin/activity-log/

## 📁 Project Structure

```
SSElectricals/
├── firstApp/
│   ├── models.py              # Data models including AdminSession & AdminActivityLog
│   ├── views.py               # Views including AJAX endpoints
│   ├── admin_views.py         # Custom admin dashboard views
│   ├── forms.py               # Enhanced forms with validators
│   ├── validators.py          # Custom validation functions
│   ├── middleware.py          # Session timeout & activity logging middleware
│   ├── admin.py               # Admin panel configuration
│   ├── urls.py                # URL routing
│   └── templates/
│       ├── firstApp/          # User-facing templates
│       └── admin/             # Custom admin templates
├── static/
│   ├── js/
│   │   ├── cart_ajax.js       # AJAX cart operations
│   │   ├── search_suggestions.js  # Dynamic search
│   │   └── validations.js     # Form validation
│   └── css/
│       └── custom.css         # Custom styling
├── SSElectricals/
│   ├── settings.py            # Project settings
│   └── urls.py                # Main URL configuration
└── manage.py
```

## 🔑 Key Technologies

- **Backend**: Django 5.x
- **Frontend**: Bootstrap 5, Custom CSS/JS
- **Database**: SQLite (default) / PostgreSQL (production)
- **Charts**: Chart.js
- **Icons**: Font Awesome 6.0
- **Animations**: Animate.css

## 📱 API Endpoints

### AJAX APIs
- `POST /api/cart/add/` - Add product to cart
- `POST /api/cart/update/` - Update cart item quantity
- `GET /api/search/?q=<query>` - Search products (returns JSON)

### Admin Endpoints
- `/admin/dashboard/` - Custom admin dashboard
- `/admin/activity-log/` - Admin activity log with filters
- `POST /admin/terminate-session/<id>/` - Terminate admin session

## ⚙ Configuration

### Session Timeout
Default: 30 minutes of inactivity  
Location: `firstApp/middleware.py` - Line 26

```python
timeout_duration = timedelta(minutes=30)  # Adjust as needed
```

### COD Order Limit
Default: 2 pending COD orders  
Location: `firstApp/views.py` - checkout view

```python
if pending_cod_orders >= 2:  # Adjust limit here
```

### Delivery Configuration
- **Area**: Indore only
- **Charge**: ₹50
- Location: `firstApp/views.py` - Line 109

## 🧪 Testing

### Test Admin Session Management
1. Login to admin panel
2. Navigate to `/admin/dashboard/`
3. Verify your session appears in "Active Admin Sessions"
4. Wait 30 minutes (or reduce timeout for testing) to test auto-logout
5. Check activity logs at `/admin/activity-log/`

### Test AJAX Functionality
1. Browse products at `/products/`
2. Click "Add to Cart" (should update without page reload)
3. Type in search box (suggestions should appear)
4. Update quantity in cart  (should update totals in real-time)

### Test Validations
1. Try signup with invalid phone/email/password
2. Attempt cart checkout with out-of-stock items
3. Place 2 COD orders, then try a 3rd (should be blocked)
4. Test form validations with JavaScript disabled

## 🔒 Security Features

- CSRF protection on all forms
- Session management with auto-timeout
- Password strength validation
- SQL injection protection (Django ORM)
- XSS protection (Django templates)
- Admin activity logging

## 📊 Database Models

### New Models
- **AdminSession**: Tracks admin login sessions
- **AdminActivityLog**: Logs all admin activities

### Existing Models
- CustomUser, Category, Product
- Cart, CartItem
- Order, OrderItem

## 🎨 Customization

### Change Theme Colors
Edit `static/css/custom.css`:
```css
/* Primary color */
.btn-warning { background-color: #YOUR_COLOR; }

/* Links and accents */
.text-warning { color: #YOUR_COLOR; }
```

### Modify Validation Rules
Edit `firstApp/validators.py` and `static/js/validations.js`

### Customize Dashboard Metrics
Edit `firstApp/admin_views.py` - `admin_dashboard` function

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Use PostgreSQL database
4. Set up static file serving
5. Configure HTTPS
6. Set `SESSION_COOKIE_SECURE = True`
7. Set up logging
8. Enable database backups

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
DEBUG=False
ALLOWED_HOSTS=your-domain.com
```

## 📝 Known Limitations

- Delivery limited to Indore only
- Payment integration is placeholder (COD/UPI/Card)
- No email notifications (coming soon)
- No inventory alerts for low stock

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Support

For issues, questions, or contributions:
- Check admin activity logs for debugging
- Review terminal output for errors
- Ensure migrations are up to date

## 📚 Version History

### v3.0.0 (Current) - December 2025 Major Upgrade
**Admin Session Management:**
- Added Django signal-based session tracking (login/logout)
- Implemented comprehensive activity logging with signals
- Enhanced middleware to attach user context to models

**Smart Validations:**
- Enhanced forms with UPI ID field and validation
- Removed COD order limit (now unlimited)
- Added password strength validation
- Implemented comprehensive validators.py functions

**Frontend Enhancements:**
- Created admin_dashboard.js with Chart.js integration
- Fixed duplicate DOCTYPE in base.html
- Added cart badge styling
- Verified existing AJAX cart and search functionality

**Files Modified:**
- `admin.py`: Added signal handlers for CRUD logging
- `middleware.py`: Enhanced with model instance tracking
- `forms.py`: Added UPI field, validators, help text
- `views.py`: Removed COD limit validation
- `admin_dashboard.js`: New file for dashboard interactivity

### v2.0.0 - Previous Features
- Added admin session management models
- Implemented AJAX cart operations
- Created custom admin dashboard
- Added smart validations
- Enhanced UI/UX with animations

### v1.0.0 - Initial Release
- Basic e-commerce functionality
- User authentication
- Product catalog
- Cart and checkout

---

**Built with ❤ using Django**
