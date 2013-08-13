from django.contrib import admin

from belfast.groupsheets.models import GroupSheet, ArchivalCollection


## config?

class GroupsheetAdmin(admin.ModelAdmin):
     list_display = ('titles', 'author', 'date', 'url')


admin.site.register(GroupSheet, GroupsheetAdmin)
admin.site.register(ArchivalCollection)