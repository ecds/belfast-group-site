from django import forms


class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    keywords = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'search-query'})
    )
