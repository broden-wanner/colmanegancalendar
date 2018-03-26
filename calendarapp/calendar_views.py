from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.utils import timezone
import datetime
import time
from .models import Year, Month, Day, Calendar, Event, Location, DayOfWeek

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

def delete_unapproved_events_after_4_days():
	for event in Event.objects.filter(approved=False):
		if event.edited_time + datetime.timedelta(days=4) < timezone.now():
			event.delete()

def calendarHomeView(request):
	delete_unapproved_events_after_4_days()
	return redirect('month', year=timezone.now().year, month=timezone.now().month)

def calendarMonthView(request, year, month):
	delete_unapproved_events_after_4_days()
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
		'today': timezone.localtime(),
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
	delete_unapproved_events_after_4_days()
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
		'locations': Location.objects.all().order_by('location'),
	})

def calendarDayView(request, year, month, day):
	delete_unapproved_events_after_4_days()
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
		'locations': Location.objects.all().order_by('location'),
	})