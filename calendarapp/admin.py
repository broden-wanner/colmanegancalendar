from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .forms import EventForm, CalendarForm
from .models import Calendar, Event, Location, Member

class EventAdmin(admin.ModelAdmin):
	exclude = ('days', 'slug')

class CalendarAdmin(admin.ModelAdmin):
	exclude = ('slug',)

class LocationAdmin(admin.ModelAdmin):
	exclude = ('slug',)

class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'member'

class UserAdmin(BaseUserAdmin):
    inlines = (MemberInline, )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Location, LocationAdmin)