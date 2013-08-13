from django.contrib import admin

from belfast.people.models import Person, Place


class PersonAdmin(admin.ModelAdmin):
     prepopulated_fields = {'slug': ('first_name', 'last_name',)}
     list_display = ('name', 'slug', 'dbpedia', 'viaf')

class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'dbpedia', 'geonames', 'latitude', 'longitude')

admin.site.register(Person, PersonAdmin)
admin.site.register(Place, PlaceAdmin)


