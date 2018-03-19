from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.http import JsonResponse
import json
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
		'locations': Location.objects.all().order_by('location'),
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
		'locations': Location.objects.all().order_by('location'),
	})

def newEventView(request):
	if request.method == 'POST':
		new_event_form = EventForm(request.POST)
		if new_event_form.is_valid():
			new_event = new_event_form.save(commit=False)
			new_event.creator = request.user
			if Group.objects.get(name='Admins') in request.user.groups.all():
				new_event.approved = True
			new_event.save()
			new_event.set_days_of_event()
			if Group.objects.get(name='Admins') in request.user.groups.all():
				return redirect('month', year=new_event.start_date.year, month=new_event.start_date.month)
			else:
				#Send email to admins if event created by non-admin
				current_site = get_current_site(request)
				subject = f'Approve Event {new_event.title} on {new_event.start_date}'
				text_message = render_to_string('email/approve_event_email.html', {
					'user': request.user,
					'domain': current_site.domain,
					'event': new_event,
				})
				html_message = render_to_string('email/approve_event_html_email.html', {
					'user': request.user,
					'domain': current_site.domain,
					'event': new_event,
				})
				recipient_list = []
				for admin in User.objects.filter(groups__name='Admins'):
					recipient_list.append(admin.email)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipient_list)
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				return redirect('event_approval_sent', slug=new_event.slug, pk=new_event.pk)

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
			'repeat_on': get_object_or_404(DayOfWeek, day_int=(timezone.localtime().weekday() + 1 if timezone.localtime().weekday() < 6 else 0)),
			'ends_on': (timezone.localtime() + datetime.timedelta(days=30)),
		})

	return render(request, 'new_event.html', {'new_event_form': new_event_form})

def event_approval_sent(request, slug, pk):
	return render(request, 'approve/event_approval_sent.html')

def approve_event(request, slug, pk):
	event = get_object_or_404(Event, slug=slug, pk=pk)
	if Group.objects.get(name='Admins') in request.user.groups.all():
		event.approved = True
		event.save()
		return redirect('month', year=event.start_date.year, month=event.start_date.month)
	else:
		return render(request, 'approve/event_disapproved.html')

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
	if request.user.is_authenticated:
		return redirect('home')
	if request.method == 'POST':
		form = MemberCreationForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			user.is_active = False
			user.save()
			user.refresh_from_db()
			user.member.calendar_preferences.set(form.cleaned_data.get('calendar_preferences'))
			user.save()
			current_site = get_current_site(request)
			subject = 'Activate Your Colman-Egan Calendar Account'
			message = render_to_string('email/account_activation_email.html', {
				'user': user,
				'domain': current_site.domain,
				'uid': force_text(urlsafe_base64_encode(force_bytes(user.pk))),
				'token': account_activation_token.make_token(user),
			})
			user.email_user(subject, message)
			return redirect('account_activation_sent')
	else:
		form = MemberCreationForm()
	return render(request, 'registration/signup.html', {'form': form})

def member_view(request, username):
	created_events = Event.objects.filter(creator=request.user).order_by('start_date', 'start_time')
	return render(request, 'registration/member_view.html', {'created_events': created_events})

def account_activation_sent(request):
	return render(request, 'registration/account_activation_sent.html')

def activate(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None

	if user is not None and account_activation_token.check_token(user, token):
		user.is_active = True
		user.member.email_confirmed = True
		user.save()
		login(request, user)
		return redirect('home')
	else:
		return render(request, 'registration/account_activation_invalid.html')

def edit_member_info(request, username):
	if request.method == 'POST':
		form = MemberChangeForm(request.POST, instance=request.user)
		if form.is_valid():
			user = form.save(commit=False)
			if form.has_changed():
				if 'email' in form.changed_data:
					logout(request)
					user.is_active = False
					user.email_confirmed = False
					user.save()
					user.refresh_from_db()
					user.member.calendar_preferences.set(form.cleaned_data.get('calendar_preferences'))
					user.save()
					current_site = get_current_site(request)
					subject = 'Colman-Egan Calendar Account Email Changed'
					message = render_to_string('email/account_change_email.html', {
						'user': user,
						'domain': current_site.domain,
						'uid': force_text(urlsafe_base64_encode(force_bytes(user.pk))),
						'token': account_activation_token.make_token(user),
					})
					user.email_user(subject, message)
					return redirect('account_email_change_sent')
			user.save()
			user.refresh_from_db()
			user.member.calendar_preferences.set(form.cleaned_data.get('calendar_preferences'))
			user.save()
			return redirect('member_view', username=username)
	else:
		form = MemberChangeForm(instance=request.user, initial={'calendar_preferences': request.user.member.calendar_preferences.all()})
	return render(request, 'registration/edit_profile.html', {'form': form})

def account_email_change_sent(request):
	return render(request, 'registration/account_email_change_sent.html')