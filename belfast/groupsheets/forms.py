from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from eulcommon.searchutil import search_terms


class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    kw_help = '''enter one or more terms;
    use * or ? for wildcards, quotes for an "exact phrase"'''
    keywords = forms.CharField(
        help_text=kw_help,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'class': 'search-query',
            'autocomplete': 'off',
            'data-toggle': 'tooltip',
            'data-placement': 'bottom',
            'data-original-title': kw_help
        })
    )

    def clean_keywords(self):
        data = self.cleaned_data['keywords']
        # doesn't care about mis-matched quotes, just strips them out
        terms = search_terms(data)
        # NOTE: this cleans up mismatched quotes and converts them to terms
        data = ' '.join('"%s"' % t if ' ' in t else t for t in terms)
        return data
