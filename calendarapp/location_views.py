from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils import timezone
from django.template.loader import render_to_string
from .models import Event, Location
from .forms import LocationForm, ReasonForm
from django.conf import settings
from django.contrib.auth.decorators import login_required

def location_view(request, slug):
	location = get_object_or_404(Location, slug=slug)
	events = Event.objects.filter(approved=True, location=location, end_date__gte=timezone.localtime().date()).order_by('start_date', 'start_time')
	return render(request, 'location_view.html', {'location': location, 'events': events})

@login_required
def new_location(request):
	if request.method == 'POST':
		new_location_form = LocationForm(request.POST)
		if new_location_form.is_valid():
			new_location = new_location_form.save(commit=False)
			new_location.creator = request.user
			if Group.objects.get(name='Admins') in request.user.groups.all():
				new_location.approved = True
			new_location.save()
			if Group.objects.get(name='Admins') in request.user.groups.all():
				return redirect('home')
			else:
				#Send email to admins if event created by non-admin
				current_site = get_current_site(request)
				subject = f'Approve Location: {new_location.location}'
				content = {
					'user': request.user,
					'domain': current_site.domain,
					'location': new_location,
				}
				message = render_to_string('email/approve_location_email.html', content)
				recipient_list = []
				for admin in User.objects.filter(groups__name='Admins'):
					recipient_list.append(admin.email)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
				return redirect('location_approval_sent', slug=new_location.slug)
	else:
		new_location_form = LocationForm()

	return render(request, 'new_location.html', {'new_location_form': new_location_form})

@login_required
def location_approval_sent(request, slug):
	return render(request, 'approve/message.html', {'message': 'Your location is pending Admin approval.'})

@login_required
def approve_location(request, slug):
	location = get_object_or_404(Location, slug=slug)
	if Group.objects.get(name='Admins') in request.user.groups.all():
		#Send an email to the user if their email is confirmed to tell them about the location
		if location.approved == False:
			location.approved = True
			location.save()
			subject = f'Location Approved: {location.location}'
			content = {
				'location': location,
				'greeting': f'Hi, {location.creator.username}. The following location has been approved:',
			}
			message = render_to_string('email/location_email.html', content)
			send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [location.creator.email])
			return redirect('home')
		#If already approved, don't send email and tell user that it is already approved
		else:
			return render(request, 'approve/message.html', {'message': 'This location has already been approved'})
	else:
		return render(request, 'approve/message.html', {'message': 'There was an error in approving the location. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def reject_location(request, slug):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		if request.method == 'POST':
			reason_form = ReasonForm(request.POST, label='Reason for rejecting the location:')
			if reason_form.is_valid():
				try:
					location = Location.objects.get(slug=slug)
				except Location.DoesNotExist:
					return render(request, 'approve/message.html', {'message': 'This location has already been rejected'})
				#Don't delete if the location is approved
				if location.approved:
					return render(request, 'approve/message.html', {'message': 'This location has already been approved'})
				#Send an email to the user if their email is confirmed to tell them about the location
				reason = reason_form.cleaned_data.get('reason')
				subject = f'Location Rejected: {location.location}'
				content = {
					'location': location,
					'reason': reason,
					'greeting': f'Hi, {location.creator.username}. The following location has been rejected for the following reason:',
				}
				message = render_to_string('email/location_email.html', content)
				send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [location.creator.email])
				location.delete()
				return redirect('home')
		else:
			reason_form = ReasonForm(label='Reason for rejecting the location:')
			return render(request, 'approve/reason_for_reject.html', {'reason_form': reason_form})
	return render(request, 'approve/message.html', {'message': 'There was an error in approving the location. Be sure you are logged in as an Admin and click the link in the email again.'})

@login_required
def edit_location(request, slug):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		location = get_object_or_404(Location, slug=slug)
		if request.method == "POST":
			location_form = LocationForm(request.POST, instance=location)
			if location_form.is_valid():
				location = location_form.save(commit=False)
				location.approved = True
				location.save()
				return redirect('location_view', slug=location.slug)
		else:
			location_form = LocationForm(instance=location)
		return render(request, 'edit_location.html', {'location_form': location_form})
	else:
		return render(request, 'not_allowed.html')

@login_required
def delete_location(request, slug):
	if Group.objects.get(name='Admins') in request.user.groups.all():
		location = get_object_or_404(Location, slug=slug)
		if request.method == "POST":
			location.delete()
			return redirect('home')
		return render(request, 'delete_location.html', {'location': location})
	else:
		return render(request, 'not_allowed.html')