from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.utils import timezone
import datetime
import time
from .models import Year, Month, Day, Calendar, Event, Location, DayOfWeek
from .forms import EventForm, CalendarForm

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

	return render(request, 'month.html', {
		'month_weeks': calendar_rows,
		'current_month': current_month,
		'next_month': next_month,
		'previous_month': previous_month,
		'calendars': Calendar.objects.all().order_by('event_calendar'),
		'locations': Location.objects.all().order_by('location')
	})

def calendarWeekView(request, year, month, first_day_of_week):
	this_year = get_object_or_404(Year, year=year)
	this_month = get_object_or_404(Month, year=this_year, month=month)
	first_day = get_object_or_404(Day, month=this_month, day_of_month=first_day_of_week)
	week = Day.objects.filter(id__gte=first_day.id, id__lte=first_day.id + 6)
	first_day_of_next_week = get_object_or_404(Day, pk=first_day.id+7)
	first_day_of_last_week = get_object_or_404(Day, pk=first_day.id-7)

	return render(request, 'week.html', {
		'week': week,
		'first_day_of_next_week': first_day_of_next_week,
		'first_day_of_last_week': first_day_of_last_week
	})

def calendarDayView(request, year, month, day):
	this_year = get_object_or_404(Year, year=year)
	this_month = get_object_or_404(Month, year=this_year, month=month)
	this_day = get_object_or_404(Day, month=this_month, day_of_month=day)
	return render(request, 'day.html', {'day': this_day})

def newEventView(request):
	if request.method == 'POST':
		new_event_form = EventForm(request.POST)
		if new_event_form.is_valid():
			new_event = new_event_form.save()
			new_event.set_days_of_event()
			return redirect('month', year=new_event.start_date.year, month=new_event.start_date.month)
	else:
		new_event_form = EventForm(initial={
			'start_date': timezone.now().strftime('%Y-%m-%d'),
			'end_date': timezone.now().strftime('%Y-%m-%d'),
			'start_time': datetime.datetime.now().strftime('%H:%M'),
			'end_time': (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime('%H:%M'),
			'repeat_every': 1,
			'duration': 2,
			'repeat_on': get_object_or_404(DayOfWeek, day_int=timezone.now().weekday() + 1 if timezone.now().weekday() < 7 else 0),
			'ends_on': (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
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
			new_calendar_form.save()
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