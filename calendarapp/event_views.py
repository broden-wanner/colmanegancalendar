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
from .forms import EventForm, CalendarForm, MemberCreationForm, MemberChangeForm, ReasonForEventEditForm, ReasonForEventRejectForm, ReasonForEventDeleteForm, ReasonForEventDeleteRejectForm
from django.conf import settings
from django.contrib.auth.decorators import login_required

def event_conflicts(test_event, original_event=None):
	test_event_start_datetime = datetime.datetime.combine(test_event.start_date, test_event.start_time)
	test_event_end_datetime = datetime.datetime.combine(test_event.end_date, test_event.end_time)
	conflicts = []
	if original_event:
		events_to_search = Event.objects.exclude(pk__in=[test_event.pk, original_event.pk]).exclude(all_day=True).exclude(approved=False)
	else:
		events_to_search = Event.objects.exclude(pk=test_event.pk).exclude(all_day=True).exclude(approved=False)
	for event in events_to_search:
		event_start_datetime = datetime.datetime.combine(event.start_date, event.start_time)
		event_end_datetime = datetime.datetime.combine(event.end_date, event.end_time)
		condition_1 = test_event_start_datetime <= event_end_datetime and test_event_start_datetime >= event_start_datetime
		condition_2 = test_event_end_datetime <= event_end_datetime and test_event_end_datetime >= event_start_datetime
		if condition_1 or condition_2:
			conflicts.append(event)
	if len(conflicts) == 0:
		return None
	return conflicts

def calendarEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	return render(request, 'event_view.html', {'event': event})

@login_required
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
				this_event_conflicts = event_conflicts(new_event)
				subject = f'Approve Event: {new_event.title} on {new_event.start_date}'
				content = {
					'user': request.user,
					'domain': current_site.domain,
					'event': new_event,
					'event_conflicts': this_event_conflicts,
				}
				text_message = render_to_string('email/approve_event_email.html', content)
				html_message = render_to_string('email/approve_event_html_email.html', content)
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

@login_required
def event_approval_sent(request, slug, pk):
	return render(request, 'approve/event_approval_sent.html')

@login_required
def approve_event(request, slug, pk):
	event = get_object_or_404(Event, slug=slug, pk=pk)
	if Group.objects.get(name='Admins') in request.user.groups.all():
		#Send an email to the user if their email is confirmed to tell them about the event
		if event.approved == False:
			event.approved = True
			event.save()
			current_site = get_current_site(request)
			subject = f'Event Approved: {event.title} on {event.start_date}'
			content = {
				'user': event.creator,
				'event': event,
			}
			text_message = render_to_string('email/event_approved_email.html', content)
			html_message = render_to_string('email/event_approved_html_email.html', content)
			msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [event.creator.email])
			msg.attach_alternative(html_message, 'text/html')
			msg.send()
			return redirect('month', year=event.start_date.year, month=event.start_date.month)
		#If already approved, don't send email and tell user that it is already approved
		else:
			return render(request, 'approve/event_already_approved.html')
	else:
		return render(request, 'approve/event_approval_error.html')

@login_required
def reject_event(request, slug, pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForEventRejectForm(request.POST)
			if reason_form.is_valid():
				try:
					event = Event.objects.get(slug=slug, pk=pk)
				except Event.DoesNotExist:
					return render(request, 'approve/event_already_rejected.html')
				#Don't delete if it is already approved
				if event.approved:
					return render(request, 'approve/event_already_approved.html')
				#Send an email to the user if their email is confirmed to tell them about the event
				reason = reason_form.cleaned_data.get('reason')
				subject = f'Event Rejected: {event.title} on {event.start_date}'
				content = {
					'user': event.creator,
					'event': event,
					'reason': reason,
				}
				text_message = render_to_string('email/event_rejected_email.html', content)
				html_message = render_to_string('email/event_rejected_html_email.html', content)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [event.creator.email])
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				event.delete()
				return redirect('month', year=event.start_date.year, month=event.start_date.month)
		else:
			reason_form = ReasonForEventRejectForm()
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	return render(request, 'approve/event_approval_error.html')

@login_required
def editEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	if request.method == 'POST':
		event_form = EventForm(request.POST, instance=event)
		reason_form = ReasonForEventEditForm(request.POST)
		if reason_form:
			if reason_form.is_valid():
				reason = reason_form.cleaned_data.get('reason')
		if event_form.is_valid():
			if event_form.has_changed():
				changed_event = event_form.save(commit=False)
				changed_event.editor = request.user
				changed_event.edited_time = timezone.now()
				changed_event.save()
				changed_event.set_days_of_event()
				original_event = Event.objects.get(pk=request.session['original_event_pk'])
				if Group.objects.get(name='Admins') in request.user.groups.all():
					changed_event.approved = True
					original_event.delete()
				else:
					changed_event.approved = False
					original_event.approved = True
					original_event.save()
				changed_event.save()
				if Group.objects.get(name='Admins') in request.user.groups.all():
					return redirect('month', year=changed_event.start_date.year, month=changed_event.start_date.month)
				else:
					#Send email to admins if event edited by non-admin
					current_site = get_current_site(request)
					subject = f'Approve Event Edit: {changed_event.title} on {changed_event.start_date}'
					content = {
						'user': request.user,
						'domain': current_site.domain,
						'changed_event': changed_event,
						'changed_event_conflicts': event_conflicts(changed_event, original_event),
						'original_event': original_event,
						'original_event_conflicts': event_conflicts(original_event),
						'reason': reason,
					}
					text_message = render_to_string('email/approve_event_edit_email.html', content)
					html_message = render_to_string('email/approve_event_edit_html_email.html', content)
					recipient_list = []
					for admin in User.objects.filter(groups__name='Admins'):
						recipient_list.append(admin.email)
					msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipient_list)
					msg.attach_alternative(html_message, 'text/html')
					msg.send()
					return redirect('event_approval_sent', slug=changed_event.slug, pk=changed_event.pk)
			else:
				#If event data hasn't changed, delete copy and redirect
				try:
					Event.objects.get(pk=request.session['original_event_pk']).delete()
				except Event.DoesNotExist:
					pass
				return redirect('month', year=event.start_date.year, month=event.start_date.month)
	else:
		event_form = EventForm(instance=event)
		if Group.objects.get(name='Admins') in request.user.groups.all():
			reason_form = None
		else:
			reason_form = ReasonForEventEditForm()
		#Creates copy of event and stores it in session data
		if 'original_event_pk' in request.session:
			#Delete the key
			del request.session['original_event_pk']
			#Create event copy
			event.pk = None
			#Adds new primary key to new event
			event.save()
			event.set_days_of_event()
			event.approved = False
			event.save()
			#Store new copy event in the session data
			request.session['original_event_pk'] = event.pk
		else:
			#If there is no key, create copy event and store it in sessions
			event.pk = None
			event.save()
			event.set_days_of_event()
			event.approved = False
			event.save()
			request.session['original_event_pk'] = event.pk
			
	return render(request, 'edit_event.html', {'event_form': event_form, 'reason_form': reason_form})

@login_required
def approve_event_change(request, original_slug, original_pk, changed_slug, changed_pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		try:
			Event.objects.get(slug=original_slug, pk=original_pk).delete()
		except Event.DoesNotExist:
			return render(request, 'approve/event_already_approved.html')
		changed_event = get_object_or_404(Event, slug=changed_slug, pk=changed_pk)
		changed_event.approved = True
		changed_event.save()
		#Send an email to the user if their event change is confirmed to tell them about the event
		subject = f'Event Change Approved: {changed_event.title} on {changed_event.start_date}'
		content = {'event': changed_event}
		text_message = render_to_string('email/event_change_approved_email.html', content)
		html_message = render_to_string('email/event_change_approved_html_email.html', content)
		recipients = []
		if changed_event.editor != changed_event.creator:
			recipients.append(changed_event.creator.email)
		recipients.append(changed_event.editor.email)
		msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipients)
		msg.attach_alternative(html_message, 'text/html')
		msg.send()
		return redirect('month', year=changed_event.start_date.year, month=changed_event.start_date.month)
	else:
		return render(request, 'approve/event_approval_error.html')

@login_required
def reject_event_change(request, original_slug, original_pk, changed_slug, changed_pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForEventRejectForm(request.POST)
			if reason_form.is_valid():
				try:
					changed_event = Event.objects.get(slug=changed_slug, pk=changed_pk)
					original_event = Event.objects.get(slug=original_slug, pk=original_pk)
				except Event.DoesNotExist:
					return render(request, 'approve/event_already_rejected.html')
				original_event.approved = True
				original_event.save()
				#Send an email to the user if their event is denied
				reason = reason_form.cleaned_data.get('reason')
				subject = f'Event Change Rejected: {changed_event.title} on {changed_event.start_date}'
				content = {
					'event': changed_event,
					'reason': reason,
				}
				text_message = render_to_string('email/event_change_rejected_email.html', content)
				html_message = render_to_string('email/event_change_rejected_html_email.html', content)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [changed_event.editor.email])
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				changed_event.delete()
				return redirect('month', year=original_event.start_date.year, month=original_event.start_date.month)
		else:
			reason_form = ReasonForEventRejectForm()
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	return render(request, 'approve/event_approval_error.html')

@login_required
def deleteEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	if request.method == 'POST':
		if Group.objects.get(name='Admins') in request.user.groups.all():
			event.delete()
			return redirect('month', year=timezone.now().year, month=timezone.now().month)
		else:
			reason_form = ReasonForEventDeleteForm(request.POST)
			if reason_form.is_valid():
				#Send email to admins if event edited by non-admin
				reason = reason_form.cleaned_data.get('reason')
				current_site = get_current_site(request)
				subject = f'Delete Event: {event.title} on {event.start_date}'
				content = {
					'user': request.user,
					'domain': current_site.domain,
					'event': event,
					'event_conflicts': event_conflicts(event),
					'reason': reason,
				}
				text_message = render_to_string('email/approve_event_delete_email.html', content)
				html_message = render_to_string('email/approve_event_delete_html_email.html', content)
				recipient_list = []
				for admin in User.objects.filter(groups__name='Admins'):
					recipient_list.append(admin.email)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipient_list)
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				return redirect('event_deletion_request_sent', slug=event.slug, pk=event.pk)
	else:
		if Group.objects.get(name='Admins') in request.user.groups.all():
			reason_form = None
		else:
			reason_form = ReasonForEventDeleteForm()
	return render(request, 'delete_event.html', {'event': event, 'reason_form': reason_form})

@login_required
def event_deletion_request_sent(request, slug, pk):
	return render(request, 'approve/event_deletion_request_sent.html')

@login_required
def approve_event_delete(request, slug, pk, deleting_user_pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForEventDeleteForm(request.POST)
			if reason_form.is_valid():
				try:
					event = Event.objects.get(slug=slug, pk=pk)
				except Event.DoesNotExist:
					return render(request, 'approve/event_already_deleted.html')
				reason = reason_form.cleaned_data.get('reason')
				deleting_user = get_object_or_404(User, pk=deleting_user_pk)
				subject = f'Event Deleted: {event.title} on {event.start_date}'
				content = {
					'deleting_user': deleting_user,
					'event': event,
					'reason': reason,
				}
				text_message = render_to_string('email/event_delete_approved_email.html', content)
				html_message = render_to_string('email/event_delete_approved_html_email.html', content)
				recipients = []
				if event.creator != deleting_user:
					recipients.append(event.creator.email)
				recipients.append(deleting_user.email)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipients)
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				event.delete()
				return redirect('month', year=event.start_date.year, month=event.start_date.month)
		else:
			reason_form = ReasonForEventDeleteForm()
			return render(request, 'approve/reason_for_delete.html', {'reason_form': reason_form})
	else:
		return render(request, 'approve/event_approval_error.html')

@login_required
def reject_event_delete(request, slug, pk, deleting_user_pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForEventDeleteRejectForm(request.POST)
			if reason_form.is_valid():
				try:
					event = Event.objects.get(slug=slug, pk=pk)
				except Event.DoesNotExist:
					return render(request, 'approve/event_already_deleted.html')
				reason = reason_form.cleaned_data.get('reason')
				deleting_user = get_object_or_404(User, pk=deleting_user_pk)
				subject = f'Event Not Deleted: {event.title} on {event.start_date}'
				content = {
					'deleting_user': deleting_user,
					'event': event,
					'reason': reason,
				}
				text_message = render_to_string('email/event_delete_rejected_email.html', content)
				html_message = render_to_string('email/event_delete_rejected_html_email.html', content)
				msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [deleting_user.email])
				msg.attach_alternative(html_message, 'text/html')
				msg.send()
				return redirect('month', year=event.start_date.year, month=event.start_date.month)
		else:
			reason_form = ReasonForEventDeleteRejectForm()
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	else:
		return render(request, 'approve/event_approval_error.html')