from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.simple_tag()
def pagination_links(template_url):
    urls_to_include = ['/day', '/month', '/week']
    for url in urls_to_include:
        if url in template_url:
            return True
    return False

@register.simple_tag()
def new_links(template_url):
	urls_to_exclude = ['/edit', '/delete']
	for url in urls_to_exclude:
		if url in template_url:
			return False

	urls_to_include = ['/day', '/month', '/week', '/event', '/calendar', '/view', '/location', '/pending']
	for url in urls_to_include:
		if url in template_url:
			return True
	return False

@register.filter(name='in_group') 
def in_group(user, group_name):
	group =  Group.objects.get(name=group_name) 
	return group in user.groups.all()