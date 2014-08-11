from django import forms
from django.contrib import admin
from eulcommon.djangoextras.formfields import DynamicSelect

from belfast.people.models import ProfilePicture
from belfast.people.rdfmodels import profile_people
from belfast.groupsheets.rdfmodels import archival_collections

def profile_persons():
    # generate a list of (uri, name) choices based on people with profiles on the site
    # NOTE: could filter out anyone with a profile picture, but that would break
    # for editing existing records

    # NOTE: make sure uri is converted to string or else initial value won't match
    choices = [(str(p.identifier), '%s, %s' % (p.lastname, p.firstname)) for p in profile_people()]
    return choices


def collections():
    # generate a list of (uri, name) choices for collections
    # (empty choice at the beginning because this field is optional)
    choices = [('', '')] + \
        [(str(c.access_url), c.name) for c in sorted(archival_collections(), key=lambda c: c.name)]
    return choices


class ProfilePictureAdminForm(forms.ModelForm):
    class Meta:
        model = ProfilePicture
        widgets = {
            'person_uri': DynamicSelect(choices=profile_persons),
            'collection_uri': DynamicSelect(choices=collections),
        }


class ProfilePictureAdmin(admin.ModelAdmin):
    form = ProfilePictureAdminForm
    list_display = ('title', 'person', 'creator', 'date', 'publisher', 'collection')


admin.site.register(ProfilePicture, ProfilePictureAdmin)
