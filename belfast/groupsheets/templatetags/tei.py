"""
Custom template filters for converting TEI tags to HTML.
"""

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from eulxml.xmlmap.teimap import TEI_NAMESPACE

__all__ = ['format_tei']

register = template.Library()

XLINK_NAMESPACE = 'http://www.w3.org/1999/xlink'
EXIST_NAMESPACE = 'http://exist.sourceforge.net/NS/exist'

# rend attributes which can be converted to simple tags
# - key is render attribute, value is tuple of start/end tag or
#   other start/end wrapping strings
rend_attributes = {
    # 'bold': ('<span class="tei-bold">', '</span>'),
    # 'italic': ('<span class="tei-italic">', '</span>'),
    # 'doublequote': ('"', '"'),
}

# TODO: support rendX
#   <l rend="indent12">Then one hot day when fields were rank</l>

# tag names that can be converted to simple tags
# - key is tag name (with namespace), value is a tuple of start/end tag
simple_tags = {
    '{%s}lg' % TEI_NAMESPACE: ('<div class="linegroup">', '</div>'),
    '{%s}l' % TEI_NAMESPACE: ('<p>', '</p>'),
    '{%s}head' % TEI_NAMESPACE: ('<strong>', '</strong>'),
    '{%s}epigraph' % TEI_NAMESPACE: ('<div class="epigraph">', '</div>'),
    '{%s}q' % TEI_NAMESPACE: ('<blockquote>', '</blockquote>'),
    #? bibl ?
}

# TODO: how do we want to support add/gap/unclear etc ?

@register.filter(needs_autoescape=True)
def format_tei(value, autoescape=None):
    """
    Custom django filter to convert structured fields in TEI XML objects to
    HTML. :class:`~eulcore.xmlmap.XmlObject` values are recursively
    processed, escaping text nodes and converting elements to <span> objects
    where appropriate. Other values are simply converted to unicode and
    escaped.
    """
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x

    if hasattr(value, 'node'):
        result = format_node(value.node, esc)
    else:
        result = ''

    return mark_safe(result)


def format_node(node, escape):
    '''Recursive method to generate HTML with the text and any
    formatting for the contents of an EAD node.

    :param node: lxml element or node to be converted from EAD to HTML
    :param escape: template escape method to be used on node text content
    :returns: string with the HTML output
    '''
    # find any start/end tags for the current element

    # check for supported rend attributes
    rend = node.get('rend', None)

    # convert display/formatting
    if rend is not None:

        if rend in rend_attributes.keys():
            s, e = rend_attributes[rend]
            start += s
            end = e + end

        # special case: some poetry is tagged with rend=indentX
        # where X is the number of spaces to be indented
        elif rend.startswith('indent'):
            # indent## - ## is number of spaces
            # for now, considering space ~= 1/2 em
            start = '<span style="padding-left:%.1fem">' % \
                    (float(rend[len('indent'):])/2)
            end = '</span>'

    # simple tags that can be converted to html markup
    elif node.tag in simple_tags.keys():
        start, end = simple_tags[node.tag]

    # more complex tags
    # elif node.tag in other_tags.keys():
    #     start, end = other_tags[node.tag](node)

    # unsupported tags that do not get converted
    else:
        start, end = '', ''


    # list of text contents to be compiled
    contents = [start]  # start tag
    # include any text directly in this node, before the first child
    if node.text is not None:
        contents.append(escape(node.text))

    # format any child nodes and add to the list of text
    contents.extend([format_node(el, escape)
                     for el in node.iterchildren()])

    # end tag for this node + any tail text
    contents.extend([end, escape(node.tail or '')])
    return ''.join(contents)
