from django.contrib import admin
from .models import Calendar, Event

class EventAdmin(admin.ModelAdmin):
	exclude = ('days', 'date_created')

admin.site.register(Calendar)
admin.site.register(Event, EventAdmin)