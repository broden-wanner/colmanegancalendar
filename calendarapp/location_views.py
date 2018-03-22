from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils import timezone
import datetime
import time
from django.template.loader import render_to_string
from .models import Year, Month, Day, Calendar, Event, Location, DayOfWeek
from .forms import EventForm, CalendarForm, MemberCreationForm, MemberChangeForm
from django.conf import settings

def locationView(request, slug):
	location = get_object_or_404(Location, slug=slug)
	events = Event.objects.filter(location=location).order_by('start_date', 'start_time')
	return render(request, 'location_view.html', {'location': location, 'events': events})