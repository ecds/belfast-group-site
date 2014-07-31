import datetime
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def natural_date(date):
    '''Display human readable date (01 Feb, 2002) for an ISO date in format
    YYYY-MM-DD, YYYY-MM, or YYYY.'''

    # return YYYY/YYYY as is
    if '-' not in date and '/' in date:
        return date

    try:
        date_parts = date.split('-')
        date_parts = [int(v) for v in date_parts]
        # year only: no modification needed
        if len(date_parts) == 1 or date_parts[1] == 0:  # also handle YYYY-00-00
            return '%s' % date_parts[0]
        elif len(date_parts) == 2 or date_parts[2] == 0:
            d = datetime.date(date_parts[0], date_parts[1], 1)
            return d.strftime('%b %Y')
        else:
            d = datetime.date(*date_parts)
            # NOTE: Using 0-padded date because that is only option
            return d.strftime('%d %b %Y')


    except:
        # if anything goes wrong with parsing the date, just return it as is
        return date
