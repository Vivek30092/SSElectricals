
# 12. Email Logging System
class EmailLog(models.Model):
    """Track all email communications for audit and retry purposes"""
    EMAIL_TYPE_CHOICES = [
        ('ORDER_STATUS', 'Order Status Update'),
        ('ORDER_RECEIPT', 'Order Receipt'),
        ('DELIVERY_OTP', 'Delivery OTP'),
        ('ORDER_DELIVERED', 'Order Delivered'),
        ('APPOINTMENT_STATUS', 'Appointment Status Update'),
        ('APPOINTMENT_COMPLETE', 'Appointment Complete'),
        ('OTP_VERIFICATION', 'OTP Verification'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('RETRY', 'Retry'),
    ]
    
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPE_CHOICES)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Reference fields
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email_type', 'recipient']),
        ]
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient} - {self.status}"
