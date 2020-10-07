from django.contrib import admin
from .models import *


class EventInline(admin.StackedInline):
    model = ProjectEvent
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': [ 'name', 'is_released',]}),
        ('Status',               {'fields': [ 'riffs_status', 'solo_status', 'bass_status', 'drums_status', 'lyrics_status', 'vox_status']}),
        ('Date information', {'fields': ['created_date'], 'classes': ['collapse']}),
        ('Slug', {'fields': [ 'slug',]}),
        (None, {'fields': ['tabulature', ]}),
    ]
    prepopulated_fields = {'slug': ('name',)}
    inlines = [EventInline]


admin.site.register(Song)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Tabulature)
admin.site.register(TabulatureFile)
admin.site.register(Lyrics)
admin.site.register(ProjectResourceFile)
admin.site.register(ProjectRelatedURL)
admin.site.register(StatusValue)
admin.site.register(StatusCategory)
admin.site.register(ProjectStatusCategory)
