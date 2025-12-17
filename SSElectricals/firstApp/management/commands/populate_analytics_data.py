from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
import random
from firstApp.models import DailySales, DailyExpenditure
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate dummy data for analytics testing'

    def handle(self, *args, **options):
        # Get or create an admin user
        try:
            admin = User.objects.filter(is_staff=True).first()
            if not admin:
                admin = User.objects.create_superuser(
                    username='testadmin',
                    email='admin@test.com',
                    password='testpass123'
                )
                self.stdout.write(self.style.SUCCESS('Created test admin user'))
        except:
            admin = None
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        # DailySales.objects.all().delete()
        # DailyExpenditure.objects.all().delete()
        
        # Generate data for the past 6 months
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)
        
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        current_date = start_date
        sales_created = 0
        expenses_created = 0
        
        while current_date <= end_date:
            # Skip some random days to make data realistic
            if random.random() > 0.85:  # 15% chance of no sales (NILL day)
                current_date += timedelta(days=1)
                continue
            
            # Get weekday
            weekday = weekdays[current_date.weekday()]
            
            # Generate realistic sales data
            # Weekend sales are typically higher
            is_weekend = current_date.weekday() >= 5
            base_sales = random.randint(15000, 45000) if is_weekend else random.randint(10000, 30000)
            
            # Add some monthly variation
            month_factor = 1 + (random.random() - 0.5) * 0.3  # ±15% variation
            total_sales = int(base_sales * month_factor)
            
            # Split between online and cash (60-40 ratio with variation)
            online_pct = random.uniform(0.5, 0.7)
            online_received = int(total_sales * online_pct)
            cash_received = total_sales - online_received
            
            # Labor and delivery charges (10-20% of total)
            labor_charge = int(total_sales * random.uniform(0.05, 0.15))
            delivery_charge = int(total_sales * random.uniform(0.03, 0.10))
            
            # Create Daily Sales entry
            DailySales.objects.create(
                date=current_date,
                day=weekday,
                total_sales=total_sales,
                online_received=online_received,
                cash_received=cash_received,
                labor_charge=labor_charge,
                delivery_charge=delivery_charge,
                remark='Test data',
                admin=admin
            )
            sales_created += 1
            
            # Generate expense data (typically 40-60% of sales)
            expense_ratio = random.uniform(0.35, 0.55)
            total_expense = int(total_sales * expense_ratio)
            
            # Split expenses between online and cash
            online_expense_pct = random.uniform(0.3, 0.5)
            online_amount = int(total_expense * online_expense_pct)
            cash_amount = total_expense - online_amount
            
            # Create Daily Expenditure entry
            DailyExpenditure.objects.create(
                date=current_date,
                day=weekday,
                description='Test expense',
                online_amount=online_amount,
                cash_amount=cash_amount,
                total=total_expense,
                admin=admin
            )
            expenses_created += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {sales_created} daily sales entries'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created {expenses_created} daily expense entries'))
        self.stdout.write(self.style.SUCCESS('Test data populated! You can now view analytics.'))
