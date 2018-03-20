from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils import timezone
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import datetime
import time
from django.template.loader import render_to_string
from .tokens import account_activation_token
from .models import Year, Month, Day, Calendar, Event, Location, DayOfWeek
from .forms import EventForm, CalendarForm, MemberCreationForm, MemberChangeForm
from django.conf import settings

def calendarView(request, slug):
	calendar = get_object_or_404(Calendar, slug=slug)
	events = Event.objects.filter(calendar=calendar).order_by('start_date', 'start_time')
	return render(request, 'calendar_view.html', {'calendar': calendar, 'events': events})

def newCalendarView(request):
	if request.method == 'POST':
		new_calendar_form = CalendarForm(request.POST)
		if new_calendar_form.is_valid():
			new_calendar = new_calendar_form.save(commit=False)
			new_calendar.creator = request.user
			new_calendar.save()
			return redirect('month', year=timezone.now().year, month=timezone.now().month)
	else:
		new_calendar_form = CalendarForm()

	return render(request, 'new_calendar.html', {'new_calendar_form': new_calendar_form})

def editCalendarView(request, slug):
	calendar = get_object_or_404(Calendar, slug=slug)
	if request.method == "POST":
		calendar_form = CalendarForm(request.POST, instance=calendar)
		if calendar_form.is_valid():
			calendar = calendar_form.save(commit=False)
			calendar.save()
			return redirect('calendar_view', slug=calendar.slug)
	else:
		calendar_form = CalendarForm(instance=calendar)
	return render(request, 'edit_calendar.html', {'calendar_form': calendar_form})

def deleteCalendarView(request, slug):
	calendar = get_object_or_404(Calendar, slug=slug)
	if request.method == "POST":
		calendar.delete()
		return redirect('month', year=timezone.now().year, month=timezone.now().month)
	return render(request, 'delete_calendar.html', {'calendar': calendar})

def locationView(request, slug):
	location = get_object_or_404(Location, slug=slug)
	events = Event.objects.filter(location=location).order_by('start_date', 'start_time')
	return render(request, 'location_view.html', {'location': location, 'events': events})