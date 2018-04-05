from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.utils import timezone
import datetime
from .models import Year, Month, Day, Calendar, Event, Location

def handle_calendar_display(request):
	#Determines calendars to hide if not in the session (upon the user first navigating to the site)
	if 'hidden_calendar_pks' not in request.session:
		if request.user.is_authenticated:
			shown_calendars = request.user.member.calendar_preferences.all()
			shown_calendar_pks = [calendar.pk for calendar in shown_calendars]
			hidden_calendar_pks = [calendar.pk for calendar in Calendar.objects.exclude(pk__in=shown_calendar_pks).exclude(approved=False)]
			#If user has no preferences, display default calendars
			if not shown_calendars:
				hidden_calendar_pks = [calendar.pk for calendar in Calendar.objects.exclude(default_calendar=True).exclude(approved=False)]
				shown_calendar_pks = [calendar.pk for calendar in Calendar.objects.filter(default_calendar=True).exclude(approved=False)]
		else:
			hidden_calendar_pks = [calendar.pk for calendar in Calendar.objects.exclude(default_calendar=True).exclude(approved=False)]
			shown_calendar_pks = [calendar.pk for calendar in Calendar.objects.filter(default_calendar=True).exclude(approved=False)]

		request.session['shown_calendar_pks'] = shown_calendar_pks
		request.session['hidden_calendar_pks'] = hidden_calendar_pks

def handle_deleting_of_copied_and_unapproved_events():
	for event in Event.objects.filter(approved=False):
		#Delete event if it was created by an admin and is unapproved (this means that it's a copy)
		if Group.objects.get(name='Admins') in event.creator.groups.all():
			event.delete()
		#Delete unapproved event if it is over 4 days old
		elif event.edited_time + datetime.timedelta(days=4) < timezone.now():
			event.delete()

@xframe_options_exempt
def calendarHomeView(request):
	handle_deleting_of_copied_and_unapproved_events()
	handle_calendar_display(request)
	if request.session.get('calendar_view', None):
		if request.session['calendar_view'] == 'month':
			return redirect('month', year=request.session['last_year_visited'], month=request.session['last_month_visited'])
		elif request.session['calendar_view'] == 'week':
			return redirect('week', year=request.session['last_year_visited'], month=request.session['last_month_visited'], first_day_of_week=request.session['last_first_day_of_week_visited'])
		elif request.session['calendar_view'] == 'day':
			return redirect('day', year=request.session['last_year_visited'], month=request.session['last_month_visited'], day=request.session['last_day_visited'])
		else:
			return redirect('month', year=timezone.now().year, month=timezone.now().month)
	else:
		return redirect('month', year=timezone.now().year, month=timezone.now().month)

@xframe_options_exempt
def calendarMonthView(request, year, month):
	handle_deleting_of_copied_and_unapproved_events()
	handle_calendar_display(request)
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
		day_view_day = get_object_or_404(Day, month=Month.objects.get(year=Year.objects.get(year=timezone.localtime().year), month=timezone.localtime().month), day_of_month=timezone.localtime().day)
		first_day_of_week = timezone.localtime()
		while first_day_of_week.weekday() != 6:
			first_day_of_week -= datetime.timedelta(days=1)
		first_day_of_week = get_object_or_404(Day, month=Month.objects.get(year=Year.objects.get(year=first_day_of_week.year), month=first_day_of_week.month), day_of_month=first_day_of_week.day)
	else:
		first_day_of_week = calendar_rows[0][0]
		day_view_day = first_day_of_week

	#Adds data for session for home view
	request.session['calendar_view'] = 'month'
	request.session['last_month_visited'] = current_month.month
	request.session['last_year_visited'] = current_year.year

	return render(request, 'month.html', {
		'type_of_view': 'Month',
		'today': timezone.localtime(),
		'day_view_day': day_view_day,
		'month_weeks': calendar_rows,
		'current_month': current_month,
		'next_month': next_month,
		'previous_month': previous_month,
		'calendars': Calendar.objects.filter(approved=True).order_by('event_calendar'),
		'locations': Location.objects.filter(approved=True).order_by('location'),
		'first_day_of_week': first_day_of_week,
	})

@xframe_options_exempt
def calendarWeekView(request, year, month, first_day_of_week):
	handle_deleting_of_copied_and_unapproved_events()
	handle_calendar_display(request)
	this_year = get_object_or_404(Year, year=year)
	this_month = get_object_or_404(Month, year=this_year, month=month)
	first_day = get_object_or_404(Day, month=this_month, day_of_month=first_day_of_week)
	week = Day.objects.filter(id__gte=first_day.id, id__lte=first_day.id + 6)
	first_day_of_next_week = get_object_or_404(Day, pk=first_day.id+7)
	first_day_of_last_week = get_object_or_404(Day, pk=first_day.id-7)

	#Adds data for session for home view
	request.session['calendar_view'] = 'week'
	request.session['last_first_day_of_week_visited'] = first_day.day_of_month
	request.session['last_month_visited'] = this_month.month
	request.session['last_year_visited'] = this_year.year

	return render(request, 'week.html', {
		'type_of_view': 'Week',
		'today': timezone.localtime(),
		'week': week,
		'day_view_day': week[0],
		'first_day_of_week': week[0],
		'first_day_of_next_week': first_day_of_next_week,
		'first_day_of_last_week': first_day_of_last_week,
		'current_month': this_month,
		'calendars': Calendar.objects.filter(approved=True).order_by('event_calendar'),
		'locations': Location.objects.filter(approved=True).order_by('location'),
	})

@xframe_options_exempt
def calendarDayView(request, year, month, day):
	handle_deleting_of_copied_and_unapproved_events()
	handle_calendar_display(request)
	this_year = get_object_or_404(Year, year=year)
	this_month = get_object_or_404(Month, year=this_year, month=month)
	this_day = get_object_or_404(Day, month=this_month, day_of_month=day)
	next_day = get_object_or_404(Day, pk=this_day.pk+1)
	previous_day = get_object_or_404(Day, pk=this_day.pk-1)
	first_day_of_week = get_object_or_404(Day, day_of_week=0, pk__lte=this_day.pk, pk__gte=this_day.pk-6)

	#Adds data for session for home view
	request.session['calendar_view'] = 'day'
	request.session['last_day_visited'] = this_day.day_of_month
	request.session['last_month_visited'] = this_month.month
	request.session['last_year_visited'] = this_year.year

	return render(request, 'day.html', {
		'type_of_view': 'Day',
		'today': timezone.localtime(),
		'day': this_day,
		'day_view_day': this_day,
		'next_day': next_day,
		'previous_day': previous_day,
		'first_day_of_week': first_day_of_week,
		'current_month': this_month,
		'calendars': Calendar.objects.filter(approved=True).order_by('event_calendar'),
		'locations': Location.objects.filter(approved=True).order_by('location'),
	})

@xframe_options_exempt
def ajax_show_hide_calendars(request):
	if request.is_ajax():
		shown_calendar_pks = dict(request.GET.lists()).get('shown_calendar_pks[]', None)
		if shown_calendar_pks:
			shown_calendar_pks = [int(x) for x in shown_calendar_pks]
			hidden_calendar_pks = [x.pk for x in Calendar.objects.exclude(pk__in=shown_calendar_pks)]
		else:
			shown_calendar_pks = []
			hidden_calendar_pks = [x.pk for x in Calendar.objects.all()]
		request.session['shown_calendar_pks'] = shown_calendar_pks
		request.session['hidden_calendar_pks'] = hidden_calendar_pks
		return JsonResponse({'done': True})
	else:
		return JsonResponse({'message': "You can't do that"})