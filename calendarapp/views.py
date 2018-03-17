from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
import json
from django.utils import timezone
import datetime
import time
from .models import Year, Month, Day, Calendar, Event, Location, DayOfWeek
from .forms import EventForm, CalendarForm, MemberCreationForm

def return_calendars(request, option):
	#Determines calendars to hide
	if request.user.is_authenticated:
		shown_calendars = request.user.member.calendar_preferences.all()
		shown_calendar_pks = [calendar.pk for calendar in shown_calendars]
		hidden_calendars = Calendar.objects.exclude(pk__in=shown_calendar_pks)
		#If user has no preferences, display default calendars
		if not shown_calendars:
			hidden_calendars = Calendar.objects.exclude(default_calendar=True)
			shown_calendars = Calendar.objects.filter(default_calendar=True)
	else:
		hidden_calendars = Calendar.objects.exclude(default_calendar=True)
		shown_calendars = Calendar.objects.filter(default_calendar=True)

	if option == 'shown_calendars':
		return shown_calendars
	elif option == 'hidden_calendars':
		return hidden_calendars

def calendarHomeView(request):
	return redirect('month', year=timezone.now().year, month=timezone.now().month)

def calendarMonthView(request, year, month):
	current_year = get_object_or_404(Year, year=year)
	current_month = get_object_or_404(Month, year=current_year, month=month)		
	days_of_month = get_list_or_404(Day, month=current_month)

	number_of_days_from_previous_month = days_of_month[0].day_of_week
	number_of_days_from_next_month = 6 - days_of_month[-1].day_of_week + 7

	if month > 1:
		previous_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year), month=month-1)
		previous_month_days = Day.objects.filter(month=previous_month).order_by('day_of_month').reverse()[0:number_of_days_from_previous_month]
	elif month == 1:
		previous_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year-1), month=12)
		previous_month_days = Day.objects.filter(month=previous_month).order_by('day_of_month').reverse()[0:number_of_days_from_previous_month]
	previous_month_days = list(previous_month_days)[::-1]

	if month < 12:
		next_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year), month=month+1)
		next_month_days = Day.objects.filter(month=next_month)[0:number_of_days_from_next_month]
	elif month == 12:
		next_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year+1), month=1)
		next_month_days = Day.objects.filter(month=next_month)[0:number_of_days_from_next_month]

	calendar_rows = []
	day_index = 0
	next_day_index = 0
	for i in range(6):
		week_row = []
		if i == 0:
			for day in previous_month_days:
				week_row.append(day)
			for j in range(7 - len(previous_month_days)):
				week_row.append(days_of_month[day_index])
				day_index += 1
		elif i > 0 and i < 4:
			for j in range(7):
				week_row.append(days_of_month[day_index])
				day_index += 1
		elif i == 4 or i == 5:
			for j in range(7):
				if day_index < len(days_of_month):
					week_row.append(days_of_month[day_index])
					day_index += 1
				elif next_day_index < len(next_month_days):
					week_row.append(next_month_days[next_day_index])
					next_day_index += 1
		calendar_rows.append(week_row)

	if timezone.localtime().month == current_month.month:
		first_day_of_week = timezone.localtime()
		while first_day_of_week.weekday() != 6:
			first_day_of_week -= datetime.timedelta(days=1)
		first_day_of_week = get_object_or_404(Day, month=Month.objects.get(year=Year.objects.get(year=first_day_of_week.year), month=first_day_of_week.month), day_of_month=first_day_of_week.day)
	else:
		first_day_of_week = calendar_rows[0][0]

	return render(request, 'month.html', {
		'type_of_view': 'Month',
		'day_view_day': first_day_of_week,
		'month_weeks': calendar_rows,
		'current_month': current_month,
		'next_month': next_month,
		'previous_month': previous_month,
		'calendars': Calendar.objects.all().order_by('event_calendar'),
		'locations': Location.objects.all().order_by('location'),
		'first_day_of_week': first_day_of_week,
		'shown_calendars': return_calendars(request, 'shown_calendars'),
		'hidden_calendars': return_calendars(request, 'hidden_calendars'),
	})

def calendarWeekView(request, year, month, first_day_of_week):
	this_year = get_object_or_404(Year, year=year)
	this_month = get_object_or_404(Month, year=this_year, month=month)
	first_day = get_object_or_404(Day, month=this_month, day_of_month=first_day_of_week)
	week = Day.objects.filter(id__gte=first_day.id, id__lte=first_day.id + 6)
	first_day_of_next_week = get_object_or_404(Day, pk=first_day.id+7)
	first_day_of_last_week = get_object_or_404(Day, pk=first_day.id-7)

	return render(request, 'week.html', {
		'type_of_view': 'Week',
		'week': week,
		'day_view_day': week[0],
		'first_day_of_week': week[0],
		'first_day_of_next_week': first_day_of_next_week,
		'first_day_of_last_week': first_day_of_last_week,
		'current_month': this_month,
		'calendars': Calendar.objects.all().order_by('event_calendar'),
		'shown_calendars': return_calendars(request, 'shown_calendars'),
		'hidden_calendars': return_calendars(request, 'hidden_calendars'),
	})

def calendarDayView(request, year, month, day):
	this_year = get_object_or_404(Year, year=year)
	this_month = get_object_or_404(Month, year=this_year, month=month)
	this_day = get_object_or_404(Day, month=this_month, day_of_month=day)
	next_day = get_object_or_404(Day, pk=this_day.pk+1)
	previous_day = get_object_or_404(Day, pk=this_day.pk-1)
	first_day_of_week = get_object_or_404(Day, day_of_week=0, pk__lte=this_day.pk, pk__gte=this_day.pk-6)
	return render(request, 'day.html', {
		'type_of_view': 'Day',
		'day': this_day,
		'day_view_day': this_day,
		'next_day': next_day,
		'previous_day': previous_day,
		'first_day_of_week': first_day_of_week,
		'current_month': this_month,
		'calendars': Calendar.objects.all().order_by('event_calendar'),
		'shown_calendars': return_calendars(request, 'shown_calendars'),
		'hidden_calendars': return_calendars(request, 'hidden_calendars'),
	})

def newEventView(request):
	if request.method == 'POST':
		new_event_form = EventForm(request.POST)
		if new_event_form.is_valid():
			new_event = new_event_form.save(commit=False)
			new_event.creator = request.user
			new_event.save()
			new_event.set_days_of_event()
			return redirect('month', year=new_event.start_date.year, month=new_event.start_date.month)
	else:
		start_time = timezone.localtime()
		start_time = start_time - datetime.timedelta(seconds=start_time.minute*60)
		end_time = start_time + datetime.timedelta(hours=1)
		new_event_form = EventForm(initial={
			'start_date': start_time,
			'end_date': end_time,
			'start_time': start_time,
			'end_time': end_time,
			'repeat_every': 1,
			'duration': 2,
			'repeat_on': get_object_or_404(DayOfWeek, day_int=timezone.localtime().weekday() + 1 if timezone.localtime().weekday() < 7 else 0),
			'ends_on': (timezone.localtime() + datetime.timedelta(days=30)),
		})

	return render(request, 'new_event.html', {'new_event_form': new_event_form})

def calendarEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	return render(request, 'event_view.html', {'event': event})

def editEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	if request.method == 'POST':
		event_form = EventForm(request.POST, instance=event)
		if event_form.is_valid():
			event = event_form.save()
			event.set_days_of_event()
			return redirect('month', year=event.start_date.year, month=event.start_date.month)
	else:
		event_form = EventForm(instance=event)

	return render(request, 'edit_event.html', {'event_form': event_form})

def deleteEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	if request.method == 'POST':
		event.delete()
		return redirect('month', year=timezone.now().year, month=timezone.now().month)
	return render(request, 'delete_event.html', {'event': event})

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

def calendarView(request, slug):
	calendar = get_object_or_404(Calendar, slug=slug)
	events = Event.objects.filter(calendar=calendar).order_by('start_date', 'start_time')
	return render(request, 'calendar_view.html', {'calendar': calendar, 'events': events})

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

def signup(request):
	if request.method == 'POST':
		form = MemberCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			user.refresh_from_db()
			user.member.calendar_preferences.set(form.cleaned_data.get('calendar_preferences'))
			user.save()
			username = form.cleaned_data.get('username')
			raw_password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=raw_password)
			login(request, user)
			return redirect('home')
	else:
		form = MemberCreationForm()
	return render(request, 'registration/signup.html', {'form': form})