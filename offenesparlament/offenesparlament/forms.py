from django import forms

class SubscriptionsLoginForm(forms.Form):
    email = forms.EmailField()
