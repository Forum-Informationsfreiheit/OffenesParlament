from django import forms

class SubscriptionsLoginForm(forms.Form):
    email = forms.EmailField(
        label='Ihre E-Mail-Adresse',
        error_messages={'required': 'Bitte geben Sie Ihre E-Mail Adresse an.', 'invalid': 'Bitte geben Sie eine valide E-Mail Adresse an.'},
        widget=forms.TextInput(attrs={'placeholder': 'Ihre E-Mail-Adresse'})
    )
    message = forms.CharField(label='Ihre Nachricht', required=False, widget=forms.Textarea(attrs={'placeholder': 'Ihre Nachricht'}))
