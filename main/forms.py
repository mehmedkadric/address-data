from django import forms
from .models import Query

class QueryForm(forms.ModelForm):
    class Meta:
        model = Query
        fields = ['address']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'validate'}),
        }