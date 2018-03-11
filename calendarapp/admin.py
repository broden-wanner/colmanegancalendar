from django.contrib import admin
from .forms import EventForm, CalendarForm
from .models import Calendar, Event, Location

class EventAdmin(admin.ModelAdmin):
	exclude = ('days', 'date_created', 'slug')
	form = EventForm

class CalendarAdmin(admin.ModelAdmin):
	exclude = ('slug',)
	form = CalendarForm

class LocationAdmin(admin.ModelAdmin):
	exclude = ('slug',)

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Location, LocationAdmin)