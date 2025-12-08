# ⚡ SSElectricals - Premium E-Commerce Solution

> **A Next-Generation Django E-Commerce Platform for Electrical Products & Services**  
> *Built for performance, scalability, and a seamless user experience.*

---

## 📖 Overview

**SSElectricals** is a robust, full-featured e-commerce application designed specifically for electrical shops. It bridges the gap between traditional retail and modern digital commerce, offering a sophisticated platform for buying products, booking services, and managing comprehensive business operations.

Built with **Django 5.x**, this project leverages advanced web technologies to deliver a responsive, secure, and dynamic shopping experience. From real-time stock management to daily accounting and service bookings, every feature is crafted with precision.

---

## 🚀 Key Features

### 🛍️ Advanced Shopping Experience
- **Dynamic Cart System**: AJAX-powered cart operations for a smooth, reload-free experience.
- **Product Reviews & Ratings**: 5-star rating system with user reviews to build trust.
- **Wishlist**: Save favorite products for later purchase with a single click.
- **Live Search**: Instant product suggestions with keyboard navigation support.
- **Responsive Design**: Mobile-first architecture ensuring perfect rendering on all devices.
- **Smart Filters**: Easy product discovery through categorized browsing and sorting.

### 🔧 Services & Appointments
- **Service Booking**: Book professional services like House Wiring, Appliance Repair, etc.
- **Appointment Management**: Track appointment status, extra charges, and history.
- **Technician Allocation**: Admin can manage and update service requests.

### 🛡️ Robust Security & Authentication
- **Secure Authentication**: OTP-based Email Login and Signup for enhanced security.
- **Profile Management**: Secure profile updates and password changes via OTP verification.
- **Delivery Verification**: OTP-based delivery confirmation to ensure secure order handovers.
- **Smart Validations**: Real-time frontend and backend validation for forms and data integrity.

### 👨‍💼 Powerful Admin Dashboard
- **Dashboard Overview**: Real-time charts (Chart.js) for sales, orders, and user growth.
- **Daily Sales Tracker**: Record daily offline/online sales with auto-calculated subtotals and CSV export.
- **Expense Manager**: Track daily shop expenditures and export data for accounting.
- **Review Management**: Moderate user reviews to maintain platform quality.
- **Order Management**: Update order statuses, confirm deliveries, and manage cancellations.
- **Inventory Management**: Streamlined tools for adding, updating, and tracking products.

### 🎨 User Experience (UX)
- **Dark Mode**: specialized dark theme for comfortable night-time browsing.
- **Marquee Tech Stack**: Visual showcase of technologies used.
- **Interactive UI**: Hover effects, smooth transitions, and animated alerts.

---

## 🛠️ Technology Stack

| Category | Technologies |
|----------|--------------|
| **Backend** | Python 3.13, Django 5.2.x |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 |
| **Database** | SQLite (Dev) / PostgreSQL (Prod) |
| **Visualization** | Chart.js 4.0 |
| **Icons & UI** | Font Awesome 6.0, Animate.css |

---

## ⚙️ Installation & Setup

Follow these steps to get the project running on your local machine.

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Step-by-Step Guide

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd SSElectricals
    ```

2.  **Navigate to Project Directory**
    ```bash
    cd SSElectricals
    ```

3.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    # Activate:
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    # source venv/bin/activate
    ```

4.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Apply Database Migrations**
    ```bash
    python manage.py makemigrations firstApp
    python manage.py migrate
    ```

6.  **Create Superuser**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run Development Server**
    ```bash
    python manage.py runserver
    ```

VISIT: `http://127.0.0.1:8000/`

---

## 📂 Project Structure

```plaintext
SSElectricals/
├── firstApp/                 # Core Application Logic
│   ├── models.py             # Database Models (Products, Orders, Reviews, Sales, Expenses)
│   ├── views.py              # User Views (Shopping, Auth, Services)
│   ├── admin_views.py        # Admin Dashboard Views
│   ├── urls.py               # App Routing
│   └── templates/            # HTML Templates
├── static/                   # Static Assets (CSS, JS, Images)
├── media/                    # User Uploaded Content
├── SSElectricals/            # Project Settings
└── manage.py                 # Django Command Utility
```

---

## 📱 API Endpoints & Routes

The platform exposes several routes for dynamic interactions:

- **Shopping**:
    - `/products/` - Product Listing
    - `/wishlist/` - User Wishlist
    - `/cart/` - Shopping Cart
- **User Actions**:
    - `/product/<id>/add-review/` - Submit Review
    - `/book-appointment/` - Service Booking
- **Admin**:
    - `/shop-admin/dashboard/` - Main Dashboard
    - `/shop-admin/sales/` - Daily Sales Entry
    - `/shop-admin/expenses/` - Daily Expenditure Entry
    - `/shop-admin/reviews/` - Review Moderation

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <b>Built with ❤️ for the Electrical Community</b>
</div>
