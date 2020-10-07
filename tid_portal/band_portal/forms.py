from django import  forms


class TabulatureForm(forms.Form):
    tab_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    tab_file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control-file', 'accept':'.gpx,.gp,.gp5'}))










