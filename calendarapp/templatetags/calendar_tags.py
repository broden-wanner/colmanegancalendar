from django import template

register = template.Library()

'''@register.simple_tag()
def get_default_calendar_events(user, day):
    if user.is_authenticated:
    	sorted_calendar_events = day.sorted_events(calendar_preferences=user.member.calendar_preferences.all())
    	if sorted_calendar_events:
    		return sorted_calendar_events
    	else:
    		#Returns the default calendars if the user has no preferences
    		return day.sorted_events()
    else:
    	#Returns the default calendars for those who are not logged in
    	return day.sorted_events()'''