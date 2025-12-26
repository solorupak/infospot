from django import forms
from django.urls import reverse_lazy


class DashboardBaseForm(forms.ModelForm):
    """Base form for dashboard forms"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 4})
            else:
                field.widget.attrs.update({'class': 'form-control'})
            
            # Add placeholder text
            if hasattr(field, 'label') and field.label:
                field.widget.attrs.update({'placeholder': field.label})
    
    def add_error_classes(self):
        """Add error classes to fields with errors"""
        for field_name, field in self.fields.items():
            if field_name in self.errors:
                current_classes = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f"{current_classes} is-invalid".strip()