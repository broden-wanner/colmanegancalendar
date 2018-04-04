from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils import timezone
import datetime
import time
from django.template.loader import render_to_string
from .models import Year, Month, Day, Calendar, Event, DayOfWeek
from .forms import EventForm, ReasonForm
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
			new_event_form.save_m2m()
			new_event.set_days_of_event()
			if Group.objects.get(name='Admins') in request.user.groups.all():
				return redirect('home')
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
				message = render_to_string('email/approve_event_email.html', content)
				admin_list = [admin.email for admin in User.objects.filter(groups__name='Admins')]
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, admin_list)
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
	return render(request, 'approve/message.html', {'message': 'Your event is pending Admin approval.'})

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
			message = render_to_string('email/event_approved_email.html', content)
			send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [event.creator.email])
			return redirect('home')
		#If already approved, don't send email and tell user that it is already approved
		else:
			return render(request, 'approve/message.html', {'message': 'This event has already been approved.'})
	else:
		return render(request, 'approve/message.html', {'message': 'There was an error in approving the event. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def reject_event(request, slug, pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForm(request.POST, label='Reason for rejecting the event:')
			if reason_form.is_valid():
				try:
					event = Event.objects.get(slug=slug, pk=pk)
				except Event.DoesNotExist:
					return render(request, 'approve/message.html', {'message': 'This event has already been rejected or deleted.'})
				#Don't delete if it is already approved
				if event.approved:
					return render(request, 'approve/message.html', {'message': 'This event has already been approved.'})
				#Send an email to the user if their email is confirmed to tell them about the event
				reason = reason_form.cleaned_data.get('reason')
				subject = f'Event Rejected: {event.title} on {event.start_date}'
				content = {
					'user': event.creator,
					'event': event,
					'reason': reason,
				}
				message = render_to_string('email/event_rejected_email.html', content)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [event.creator.email])
				event.delete()
				return redirect('home')
		else:
			reason_form = ReasonForm(label='Reason for rejecting the event:')
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	return render(request, 'approve/message.html', {'message': 'There was an error in approving the event. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def editEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	if request.method == 'POST':
		event_form = EventForm(request.POST, instance=event)
		reason_form = ReasonForm(request.POST, label='Reason for editing the event:')
		if reason_form:
			if reason_form.is_valid():
				reason = reason_form.cleaned_data.get('reason')
		if event_form.is_valid():
			if event_form.has_changed():
				changed_event = event_form.save(commit=False)
				changed_event.editor = request.user
				changed_event.edited_time = timezone.now()
				#Creates entirely new event instead of updating old one
				changed_event.pk = None
				changed_event.save()
				event_form.save_m2m()
				changed_event.set_days_of_event()
				original_event = changed_event.original_event
				#If the user is an admin, delete original event and approve the changed event immediately
				if Group.objects.get(name='Admins') in request.user.groups.all():
					changed_event.approved = True
					changed_event.original_event = None
					original_event.delete()
					changed_event.save()
				else:
					changed_event.approved = False
					original_event.approved = True
					original_event.save()
					changed_event.save()
				#Redirect to home if the user is an admin
				if Group.objects.get(name='Admins') in request.user.groups.all():
					return redirect('home')
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
					message = render_to_string('email/approve_event_edit_email.html', content)
					admin_list = [admin.email for admin in User.objects.filter(groups__name='Admins')]
					send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, admin_list)
					return redirect('event_approval_sent', slug=changed_event.slug, pk=changed_event.pk)
			else:
				#If event data hasn't changed, redirect
				return redirect('home')
	else:
		event_form = EventForm(instance=event)
		if Group.objects.get(name='Admins') in request.user.groups.all():
			reason_form = None
		else:
			reason_form = ReasonForm(label='Reason for editing the event:')
		event.original_event = event
		event.save()	
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
		message = render_to_string('email/event_change_approved_email.html', content)
		recipients = []
		if changed_event.editor != changed_event.creator:
			recipients.append(changed_event.creator.email)
		recipients.append(changed_event.editor.email)
		send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
		return redirect('home')
	else:
		return render(request, 'approve/message.html', {'message': 'There was an error in approving the event. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def reject_event_change(request, original_slug, original_pk, changed_slug, changed_pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForm(request.POST, label='Reason for rejecting the event change:')
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
				message = render_to_string('email/event_change_rejected_email.html', content)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [changed_event.editor.email])
				changed_event.delete()
				return redirect('home')
		else:
			reason_form = ReasonForm(label='Reason for rejecting the event change:')
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	return render(request, 'approve/message.html', {'message': 'There was an error in approving the event. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def deleteEventView(request, year, month, day, pk, slug):
	event = get_object_or_404(Event, pk=pk, slug=slug)
	if request.method == 'POST':
		if Group.objects.get(name='Admins') in request.user.groups.all():
			event.delete()
			return redirect('home')
		else:
			reason_form = ReasonForm(request.POST, label='Reason for deleting the event:')
			if reason_form.is_valid():
				event.deleter = request.user
				event.save()
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
				message = render_to_string('email/approve_event_delete_email.html', content)
				admin_list = [admin.email for admin in User.objects.filter(groups__name='Admins')]
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, admin_list)
				return redirect('event_deletion_request_sent', slug=event.slug, pk=event.pk)
	else:
		if Group.objects.get(name='Admins') in request.user.groups.all():
			reason_form = None
		else:
			reason_form = ReasonForm(label='Reason for deleting the event:')
	return render(request, 'delete_event.html', {'event': event, 'reason_form': reason_form})

@login_required
def event_deletion_request_sent(request, slug, pk):
	return render(request, 'approve/message.html', {'message': 'Your event deletion is pending admin approval.'})

@login_required
def approve_event_delete(request, slug, pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForm(request.POST, label='Reason for deleting the event:')
			if reason_form.is_valid():
				try:
					event = Event.objects.get(slug=slug, pk=pk)
				except Event.DoesNotExist:
					return render(request, 'approve/message.html', {'message': 'This event has already been deleted.'})
				reason = reason_form.cleaned_data.get('reason')
				deleting_user = event.deleter
				subject = f'Event Deleted: {event.title} on {event.start_date}'
				content = {
					'deleting_user': deleting_user,
					'event': event,
					'reason': reason,
				}
				message = render_to_string('email/event_delete_approved_email.html', content)
				recipients = []
				if event.creator != deleting_user:
					recipients.append(event.creator.email)
				recipients.append(deleting_user.email)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
				event.delete()
				return redirect('home')
		else:
			reason_form = ReasonForm(label='Reason for deleting the event:')
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	else:
		return render(request, 'approve/message.html', {'message': 'There was an error in approving the event. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def reject_event_delete(request, slug, pk):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForm(request.POST, label='Reason for not deleting the event:')
			if reason_form.is_valid():
				try:
					event = Event.objects.get(slug=slug, pk=pk)
				except Event.DoesNotExist:
					return render(request, 'approve/event_already_deleted.html')
				reason = reason_form.cleaned_data.get('reason')
				deleting_user = event.deleter
				subject = f'Event Not Deleted: {event.title} on {event.start_date}'
				content = {
					'deleting_user': deleting_user,
					'event': event,
					'reason': reason,
				}
				message = render_to_string('email/event_delete_rejected_email.html', content)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [deleting_user.email])
				return redirect('home')
		else:
			reason_form = ReasonForm(label='Reason for not deleting the event:')
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	else:
		return render(request, 'approve/message.html', {'message': 'There was an error in approving the event. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def pending_events(request):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		pending_created_events = Event.objects.filter(approved=False, editor=None)
		pending_edited_events = Event.objects.exclude(approved=True).exclude(pk__in=[x.pk for x in pending_created_events])
		return render(request, 'pending_events.html', {
			'pending_created_events': pending_created_events,
			'pending_edited_events': pending_edited_events,
		})
	else:
		return render(request, 'not_allowed.html')

@login_required
def ajax_pending_events(request):
	if request.is_ajax():
		if request.GET.getlist('delete_reasons[]', None):
			delete_reasons = [json.loads(x) for x in request.GET.getlist('delete_reasons[]', None)]
			#print(f'delete_reasons: {delete_reasons}')
		approved_created_pks = [int(x) for x in request.GET.getlist('approved_created_pks[]')]
		#print(f'approved_created_pks: {approved_created_pks}')
		'''if approved_created_pks:
			#Send an email to all users to tell them
			for pk in approved_created_pks:
				try:
					event = Event.objects.get(pk=pk)
				except Event.DoesNotExist:
					continue
				if event.approved == False:
					event.approved = True
					event.save()
					subject = f'Event Approved: {event.title} on {event.start_date}'
					content = {
						'user': event.creator,
						'event': event,
					}
					text_message = render_to_string('email/event_approved_email.html', content)
					html_message = render_to_string('email/event_approved_html_email.html', content)
					msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [event.creator.email])
					msg.attach_alternative(html_message, 'text/html')
					msg.send()'''
		deleted_created_pks = [int(x) for x in request.GET.getlist('deleted_created_pks[]')]
		'''if deleted_created_pks:
			for pk in deleted_created_pks:
				try:
					event = Event.objects.get(pk=pk)
				except Event.DoesNotExist:
					continue
				reason = filter(lambda reason: reason['pk'] == str(pk), delete_reasons)['reason']
				deleting_user = request.user
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
				event.delete()'''
		#print(f'deleted_created_pks: {deleted_created_pks}')
		approved_edited_pks = [int(x) for x in request.GET.getlist('approved_edited_pks[]')]
		#print(f'approved_edited_pks: {approved_edited_pks}')
		deleted_edited_pks = [int(x) for x in request.GET.getlist('deleted_edited_pks[]')]
		#print(f'deleted_edited_pks: {deleted_edited_pks}')

		return JsonResponse({'done': True})
	else:
		return JsonResponse({'message': "You can't do that"})
	