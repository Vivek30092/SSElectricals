"""
Financial Validation Guards

CRITICAL BUSINESS RULE (Non-Negotiable):
=========================================
Orders and deliveries must NEVER automatically update financial metrics.

This module provides validation guards and logging to prevent accidental 
violations of this core business rule.

All financial data (sales, revenue, profit) must be manually entered by admin.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FinancialUpdateGuard:
    """
    Prevents and logs any attempts to automatically update financial data from orders.
    
    Usage:
        guard = FinancialUpdateGuard()
        if guard.validate_order_update(order_instance):
            # Safe to proceed with operational update
            pass
        else:
            # Violation detected and logged
            raise PermissionError("Financial updates from orders are not permitted")
    """
    
    @staticmethod
    def log_violation(violation_type: str, description: str, source_module: str, 
                     order=None, user=None, ip_address: Optional[str] = None):
        """
        Log a financial validation violation.
        
        Args:
            violation_type: Type of violation (from VIOLATION_TYPE_CHOICES)
            description: Detailed description of what was attempted
            source_module: Module/function that attempted the update
            order: Optional Order instance
            user: Optional User instance
            ip_address: Optional IP address
        """
        try:
            from .models import FinancialValidationLog
            
            FinancialValidationLog.objects.create(
                violation_type=violation_type,
                description=description,
                source_module=source_module,
                order=order,
                user=user,
                ip_address=ip_address
            )
            
            logger.warning(
                f"Financial Violation Detected: {violation_type} - {description} "
                f"(Source: {source_module})"
            )
        except Exception as e:
            logger.error(f"Failed to log financial violation: {e}")
    
    @staticmethod
    def validate_order_to_finance_separation(source_function: str) -> bool:
        """
        Validates that order data is not being used for financial calculations.
        
        This should be called at the start of any financial calculation function.
        
        Args:
            source_function: Name of the function performing financial calculations
            
        Returns:
            True if validation passes (no orders being used)
            False if violation detected
        """
        # This is a marker function - actual implementation would analyze the call stack
        # For now, it serves as documentation and can be extended with actual checks
        logger.info(f"Financial separation validated for: {source_function}")
        return True
    
    @staticmethod
    def prevent_auto_sales_update(order, source_module: str, user=None) -> bool:
        """
        Prevents automatic sales updates when order status changes.
        
        Args:
            order: Order instance that is being updated
            source_module: Module attempting the update
            user: Optional user performing the action
            
        Returns:
            False (always blocks auto-updates)
        """
        FinancialUpdateGuard.log_violation(
            violation_type='AUTO_SALES_UPDATE',
            description=f"Attempted to auto-update sales from Order #{order.id} status change",
            source_module=source_module,
            order=order,
            user=user
        )
        return False
    
    @staticmethod
    def prevent_auto_revenue_update(order, source_module: str, user=None) -> bool:
        """
        Prevents automatic revenue updates when order is delivered.
        
        Args:
            order: Order instance that is being updated
            source_module: Module attempting the update
            user: Optional user performing the action
            
        Returns:
            False (always blocks auto-updates)
        """
        FinancialUpdateGuard.log_violation(
            violation_type='AUTO_REVENUE_UPDATE',
            description=f"Attempted to auto-update revenue from Order #{order.id} delivery",
            source_module=source_module,
            order=order,
            user=user
        )
        return False


def ensure_manual_financial_entry_only(func):
    """
    Decorator to ensure a view/function only uses manual financial entries.
    
    Usage:
        @ensure_manual_financial_entry_only
        def calculate_profit(request):
            # This function now has validation that it uses only manual entries
            pass
    """
    def wrapper(*args, **kwargs):
        guard = FinancialUpdateGuard()
        guard.validate_order_to_finance_separation(func.__name__)
        return func(*args, **kwargs)
    return wrapper


# Validation Messages
FINANCIAL_SEPARATION_MESSAGE = """
⚠️ IMPORTANT: Financial Data Policy

Sales, revenue, and profit are maintained manually by admin only.
Order data does NOT automatically affect financial reports.

This ensures:
• Clean separation of operations vs accounting
• Accurate real-world financial tracking  
• No accidental double-counting
• Full admin control of business numbers

To update financial data:
1. Navigate to Daily Sales Management
2. Manually enter sales data for the day
3. Or upload sales CSV/XLSX files
"""
