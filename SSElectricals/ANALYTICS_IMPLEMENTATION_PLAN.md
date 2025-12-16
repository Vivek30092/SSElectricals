# Analytics Page Implementation Plan

## Overview
Creating a dedicated analytics/insights page with comprehensive sales and expense analytics.

## Phase 1: Backend View (admin_analytics)
- Aggregate sales data (KPIs, trends, payment modes)
- Aggregate expense data (KPIs, trends, payment modes)
- Combined sales vs expense metrics
- Filter handling (date range, month, admin)
- JSON serialization for Chart.js

## Phase 2: Template Structure
- Tab toggle (Sales / Expenses / Combined)
- Global filters (date range, month, admin)
- Responsive grid layout
- Chart containers with proper sizing

## Phase 3: Sales Insights Tab
### KPI Cards (5 cards):
1. Total Sales (Period)
2. Average Daily Sales
3. Online vs Cash %
4. Total Labor Charges
5. Total Delivery Charges

### Charts (7 visualizations):
1. Daily Sales Trend (Bar Chart)
2. Monthly Sales Growth (Line Chart)
3. Weekday Performance (Bar Chart)
4. Payment Mode - Stacked Bar (Online vs Cash per day)
5. Payment Mode - Pie Chart (Monthly split)
6. Cost Insights - Line Chart (Labor & Delivery over time)
7. Cost Distribution - Donut Chart

### Tables:
1. NILL/Closed days
2. Admin-wise entry count

## Phase 4: Expense Insights Tab
### KPI Cards (3 cards):
1. Total Expenses
2. Average Daily Expense
3. Online vs Cash Split %

### Charts (5 visualizations):
1. Daily Expense Trend (Line Chart)
2. Monthly Expenses (Bar Chart)
3. Payment Mode - Stacked Bar
4. Payment Mode - Pie Chart
5. Expense by Description (if categorized)

### Table:
1. Expense details with filters

## Phase 5: Combined View
### Charts (2 visualizations):
1. Sales vs Expenses Line Chart
2. Net Contribution Chart

### KPI:
1. Net Contribution with color bands

## Phase 6: Interactivity
- Filter changes update all charts
- Tab switching without page reload
- Hover tooltips
- Export functionality

## Technical Stack
- **Backend**: Django views with aggregation queries
- **Frontend**: Chart.js for all visualizations
- **Styling**: Admin theme CSS (light/dark mode)
- **State**: JavaScript for tab management and filters

## Files to Create/Modify
1. `firstApp/admin_views.py` - Add `admin_analytics` view
2. `firstApp/templates/admin/admin_analytics.html` - New template
3. `SSElectricals/urls.py` or `firstApp/urls.py` - Add route
4. `firstApp/templates/admin/base_admin.html` - Add sidebar link

## Implementation Order
1. Create view with data aggregation ✓
2. Create basic template structure ✓
3. Add Sales Insights charts ✓
4. Add Expense Insights charts ✓
5. Add Combined view ✓
6. Add filters and interactivity ✓
7. Polish UX and styling ✓
