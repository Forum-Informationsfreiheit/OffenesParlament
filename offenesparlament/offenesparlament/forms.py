from django import forms

class SubscriptionsLoginForm(forms.Form):
    email = forms.EmailField(label='Ihre E-Mail-Adresse', widget=forms.TextInput(attrs={'placeholder': 'Ihre E-Mail-Adresse'}))
