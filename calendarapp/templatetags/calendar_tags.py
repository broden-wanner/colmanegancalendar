from django import template

register = template.Library()

@register.simple_tag()
def get_default_calendar_events(user, day):
    if user.is_authenticated:
    	return day.sorted_events(calendar_preferences=user.member.calendar_preferences.all())
    else:
    	return day.sorted_events()