# Table Sorting Implementation Guide

## ✅ Backend Complete
The views are updated with sorting support. Date DESC is the default.

## 📋 Frontend Steps:

### Step 1: Add CSS to admin-theme.css
Copy content from `TABLE_SORTING_STYLES.css` and paste at the end of:
`static/css/admin-theme.css`

### Step 2: Update Daily Sales Template

In `admin_daily_sales.html`, find the `<thead>` section (around line 84) and replace the table headers with this:

```html
<thead class="bg-light text-secondary">
    <tr>
        <th scope="col" class="sortable-header {% if current_sort_by == 'date' %}sort-active{% endif %}" 
            data-column="date">
            Date 
            <span class="sort-indicator">
                {% if current_sort_by == 'date' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'day' %}sort-active{% endif %}" 
            data-column="day">
            Day
            <span class="sort-indicator">
                {% if current_sort_by == 'day' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'total_sales' %}sort-active{% endif %}" 
            data-column="total_sales">
            Total Sales (₹)
            <span class="sort-indicator">
                {% if current_sort_by == 'total_sales' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'online_received' %}sort-active{% endif %}" 
            data-column="online_received">
            Online Received (₹)
            <span class="sort-indicator">
                {% if current_sort_by == 'online_received' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'cash_received' %}sort-active{% endif %}" 
            data-column="cash_received">
            Cash Received (₹)
            <span class="sort-indicator">
                {% if current_sort_by == 'cash_received' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'labor_charge' %}sort-active{% endif %}" 
            data-column="labor_charge">
            Labor Charge (₹)
            <span class="sort-indicator">
                {% if current_sort_by == 'labor_charge' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'delivery_charge' %}sort-active{% endif %}" 
            data-column="delivery_charge">
            Delivery Charge (₹)
            <span class="sort-indicator">
                {% if current_sort_by == 'delivery_charge' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'subtotal' %}sort-active{% endif %}" 
            data-column="subtotal">
            Subtotal (₹)
            <span class="sort-indicator">
                {% if current_sort_by == 'subtotal' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col">Remark</th>
        <th scope="col" class="sortable-header {% if current_sort_by == 'admin__username' %}sort-active{% endif %}" 
            data-column="admin__username">
            Admin
            <span class="sort-indicator">
                {% if current_sort_by == 'admin__username' %}
                    {% if current_sort_order == 'asc' %}
                        <i class="fas fa-sort-up"></i>
                    {% else %}
                        <i class="fas fa-sort-down"></i>
                    {% endif %}
                {% else %}
                    <i class="fas fa-sort"></i>
                {% endif %}
            </span>
        </th>
        <th scope="col">Actions</th>
    </tr>
</thead>
```

### Step 3: Add Reset Button in Daily Sales

Add this button after the filters section (around line 60-70):

```html
<button type="button" id="resetSortBtn" class="reset-sort-btn">
    <i class="fas fa-undo me-1"></i> Reset Sorting
</button>
```

### Step 4: Add JavaScript to Daily Sales

At the bottom of `admin_daily_sales.html`, before `{% endblock %}`, add:

```html
{% block extra_js %}
{{ block.super }}
<script src="{% static 'js/table-sorting.js' %}"></script>
{% endblock %}
```

### Step 5: Repeat for Daily Expenses

Do the same changes in `admin_daily_expenses.html` with these column names:
- date
- day  
- online_amount
- cash_amount
- total
- admin__username

### Step 6: Update CSS Version

In `base_admin.html`, change CSS version to 16.0

## 🎯 Result:
- ✅ Click any column header to sort
- ✅ Arrow indicators show sort direction
- ✅ Default: Date DESC (newest first)
- ✅ Reset button to restore default
- ✅ Works with filters and pagination
