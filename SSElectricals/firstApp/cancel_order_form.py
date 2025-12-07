from django import forms

class CancelOrderForm(forms.Form):
    REASON_CHOICES = [
        ('Found better price', 'Found better price'),
        ('Delivery too slow', 'Delivery too slow'),
        ('Ordered by mistake', 'Ordered by mistake'),
        ('Other', 'Other'),
    ]
    reason = forms.ChoiceField(choices=REASON_CHOICES, widget=forms.RadioSelect, label="Select Cancellation Reason")
    other_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please describe your reason...'}),
        label="Additional Details (Optional)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get('reason')
        other_reason = cleaned_data.get('other_reason')
        
        if reason == 'Other' and not other_reason:
            self.add_error('other_reason', 'Please specify the reason.')
        return cleaned_data
