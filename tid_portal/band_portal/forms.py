from django import  forms
from django.utils.translation import gettext_lazy as _


class TabulatureForm(forms.Form):
    tab_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), label=_('Tabulature name'))
    tab_file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control-file', 'accept':'.gpx,.gp,.gp5'}), label=_('Tabulature file'))










