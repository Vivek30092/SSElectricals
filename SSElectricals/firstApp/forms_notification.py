from django import forms
from .models import Notification, CustomUser

class NotificationForm(forms.ModelForm):
    """Form for creating and editing notifications"""
    
    class Meta:
        model = Notification
        fields = ['title', 'message', 'image', 'target_type', 'target_city', 'target_area', 'target_users', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter notification title'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter notification message'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'target_type': forms.Select(attrs={'class': 'form-select'}),
            'target_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Indore'}),
            'target_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vijay Nagar'}),
            'target_users': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show regular users in target_users
        self.fields['target_users'].queryset = CustomUser.objects.filter(role='USER').order_by('username')
