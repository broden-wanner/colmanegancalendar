from django import template

register = template.Library()

@register.simple_tag()
def pagination_links(template_url):
    urls_to_include = ['/day', '/month', '/week']
    for url in urls_to_include:
        if url in template_url:
            return True
    return False

@register.simple_tag()
def new_event_or_calendar_links(template_url):
	urls_to_exclude = ['/edit', '/delete']
	for url in urls_to_exclude:
		if url in template_url:
			return False

	urls_to_include = ['/day', '/month', '/week', '/event', '/calendar']
	for url in urls_to_include:
		if url in template_url:
			return True
	return False
    