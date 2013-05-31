from belfast.groupsheets.forms import KeywordSearchForm

def searchform(request):
    "Template context processor: add the keyword search form to context"
    return {'kwsearch_form': KeywordSearchForm()}
