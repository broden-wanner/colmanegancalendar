from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils import timezone
import datetime
import time
from django.template.loader import render_to_string
from .models import Year, Month, Day, Calendar, Event, Location, DayOfWeek
from .forms import EventForm, CalendarForm, MemberCreationForm, MemberChangeForm, ReasonForCalendarRejectForm
from django.conf import settings
from django.contrib.auth.decorators import login_required

def calendarView(request, slug):
	calendar = get_object_or_404(Calendar, slug=slug)
	events = Event.objects.filter(calendar=calendar).order_by('start_date', 'start_time')
	return render(request, 'calendar_view.html', {'calendar': calendar, 'events': events})

@login_required
def newCalendarView(request):
	if request.method == 'POST':
		new_calendar_form = CalendarForm(request.POST)
		if new_calendar_form.is_valid():
			new_calendar = new_calendar_form.save(commit=False)
			new_calendar.creator = request.user
			if Group.objects.get(name='Admins') in request.user.groups.all():
				new_calendar.approved = True
			new_calendar.save()
			if Group.objects.get(name='Admins') in request.user.groups.all():
				return redirect('home')
			else:
				#Send email to admins if event created by non-admin
				current_site = get_current_site(request)
				subject = f'Approve Calendar: {new_calendar.event_calendar}'
				content = {
					'user': request.user,
					'domain': current_site.domain,
					'calendar': new_calendar,
				}
				text_message = render_to_string('email/approve_calendar_email.html', content)
				html_message = render_to_string('email/approve_calendar_html_email.html', content)
				recipient_list = []
				for admin in User.objects.filter(groups__name='Admins'):
					recipient_list.append(admin.email)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipient_list)
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				return redirect('calendar_approval_sent', slug=new_calendar.slug)
	else:
		new_calendar_form = CalendarForm()

	return render(request, 'new_calendar.html', {'new_calendar_form': new_calendar_form})

@login_required
def calendar_approval_sent(request, slug):
	return render(request, 'approve/calendar_approval_sent.html')

@login_required
def approve_calendar(request, slug):
	calendar = get_object_or_404(Calendar, slug=slug)
	if Group.objects.get(name='Admins') in request.user.groups.all():
		#Send an email to the user if their email is confirmed to tell them about the event
		if calendar.approved == False:
			calendar.approved = True
			calendar.save()
			current_site = get_current_site(request)
			subject = f'Calendar Approved: {calendar.event_calendar}'
			content = {'calendar': calendar}
			text_message = render_to_string('email/calendar_approved_email.html', content)
			html_message = render_to_string('email/calendar_approved_html_email.html', content)
			msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [calendar.creator.email])
			msg.attach_alternative(html_message, 'text/html')
			msg.send()
			return redirect('home')
		#If already approved, don't send email and tell user that it is already approved
		else:
			return render(request, 'approve/calendar_already_approved.html')
	else:
		return render(request, 'approve/calendar_approval_error.html')

@login_required
def reject_calendar(request, slug):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForCalendarRejectForm(request.POST)
			if reason_form.is_valid():
				try:
					calendar = Calendar.objects.get(slug=slug)
				except Calendar.DoesNotExist:
					return render(request, 'approve/calendar_already_rejected.html')
				#Don't delete if the calendar is approved
				if calendar.approved:
					return render(request, 'approve/calendar_already_approved.html')
				#Send an email to the user if their email is confirmed to tell them about the calendar
				reason = reason_form.cleaned_data.get('reason')
				subject = f'Calendar Rejected: {calendar.event_calendar}'
				content = {
					'calendar': calendar,
					'reason': reason,
				}
				text_message = render_to_string('email/calendar_rejected_email.html', content)
				html_message = render_to_string('email/calendar_rejected_html_email.html', content)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [calendar.creator.email])
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				calendar.delete()
				return redirect('home')
		else:
			reason_form = ReasonForCalendarRejectForm()
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	return render(request, 'approve/calendar_approval_error.html')

@login_required
def editCalendarView(request, slug):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		calendar = get_object_or_404(Calendar, slug=slug)
		if request.method == "POST":
			calendar_form = CalendarForm(request.POST, instance=calendar)
			if calendar_form.is_valid():
				calendar = calendar_form.save(commit=False)
				calendar.approved = True
				calendar.save()
				return redirect('calendar_view', slug=calendar.slug)
		else:
			calendar_form = CalendarForm(instance=calendar)
		return render(request, 'edit_calendar.html', {'calendar_form': calendar_form})
	else:
		return render(request, 'not_allowed.html')

@login_required
def deleteCalendarView(request, slug):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		calendar = get_object_or_404(Calendar, slug=slug)
		if request.method == "POST":
			calendar.delete()
			return redirect('month', year=timezone.now().year, month=timezone.now().month)
		return render(request, 'delete_calendar.html', {'calendar': calendar})
	else:
		return render(request, 'not_allowed.html')