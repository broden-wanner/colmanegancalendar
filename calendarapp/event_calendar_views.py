from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils import timezone
from django.template.loader import render_to_string
from .models import Calendar, Event
from .forms import CalendarForm, ReasonForm
from .calendar_views import handle_deleting_of_copied_and_unapproved_events
from django.conf import settings
from django.contrib.auth.decorators import login_required

def calendarView(request, slug):
	handle_deleting_of_copied_and_unapproved_events()
	calendar = get_object_or_404(Calendar, slug=slug)
	events = Event.objects.filter(approved=True, calendar=calendar, end_date__gte=timezone.localtime().date()).order_by('start_date', 'start_time')
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
				message = render_to_string('email/approve_calendar_email.html', content)
				recipient_list = []
				for admin in User.objects.filter(groups__name='Admins'):
					recipient_list.append(admin.email)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
				return redirect('calendar_approval_sent', slug=new_calendar.slug)
	else:
		new_calendar_form = CalendarForm()

	return render(request, 'new_calendar.html', {'new_calendar_form': new_calendar_form})

@login_required
def calendar_approval_sent(request, slug):
	return render(request, 'approve/message.html', {'message': 'Your calendar is pending Admin approval.'})

@login_required
def approve_calendar(request, slug):
	calendar = get_object_or_404(Calendar, slug=slug)
	if Group.objects.get(name='Admins') in request.user.groups.all():
		#Send an email to the user if their email is confirmed to tell them about the event
		if calendar.approved == False:
			calendar.approved = True
			calendar.save()
			subject = f'Calendar Approved: {calendar.event_calendar}'
			content = {
				'calendar': calendar,
				'greeting': f'Hi, {calendar.creator.username}. The following calendar has been approved:',
			}
			message = render_to_string('email/calendar_email.html', content)
			send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [calendar.creator.email])
			return redirect('home')
		#If already approved, don't send email and tell user that it is already approved
		else:
			return render(request, 'approve/message.html', {'message': 'Your calendar has already been approved.'})
	else:
		return render(request, 'approve/message.html', {'message': 'There was an error in approving the calendar. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def reject_calendar(request, slug):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForm(request.POST, label='Reason for rejecting the calendar:')
			if reason_form.is_valid():
				try:
					calendar = Calendar.objects.get(slug=slug)
				except Calendar.DoesNotExist:
					return render(request, 'approve/message.html', {'message': 'This calendar has already been rejected.'})
				#Don't delete if the calendar is approved
				if calendar.approved:
					return render(request, 'approve/message.html', {'message': 'This calendar has already been approved.'})
				#Send an email to the user if their email is confirmed to tell them about the calendar
				reason = reason_form.cleaned_data.get('reason')
				subject = f'Calendar Rejected: {calendar.event_calendar}'
				content = {
					'calendar': calendar,
					'reason': reason,
					'greeting': f'Hi, {calendar.creator.username}. The following calendar has been rejected for the following reason:',
				}
				message = render_to_string('email/calendar_email.html', content)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [calendar.creator.email])
				calendar.delete()
				return redirect('home')
		else:
			reason_form = ReasonForm(label='Reason for rejecting the calendar:')
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	return render(request, 'approve/message.html', {'message': 'There was an error in approving the calendar. Be sure you are logged in as an Admin and click the link in the email again.'})

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
			return redirect('home')
		return render(request, 'delete_calendar.html', {'calendar': calendar})
	else:
		return render(request, 'not_allowed.html')