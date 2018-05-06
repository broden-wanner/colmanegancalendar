from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from .models import Calendar, Event, Location
from .forms import MemberCreationForm, MemberChangeForm
from django.conf import settings
from django.contrib.auth.decorators import login_required
import json
import urllib
from django.contrib import messages

def signup(request):
	if request.user.is_authenticated:
		return redirect('home')
	if request.method == 'POST':
		form = MemberCreationForm(request.POST)
		if form.is_valid():
			''' Begin reCAPTCHA validation '''
			recaptcha_repsonse = request.POST.get('g-recaptcha-response')
			url = 'https://www.google.com/recaptcha/api/siteverify'
			values = {
				'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
				'response': recaptcha_repsonse
			}
			data = urllib.parse.urlencode(values).encode()
			req =  urllib.request.Request(url, data=data)
			response = urllib.request.urlopen(req)
			result = json.loads(response.read().decode())
			''' End reCAPTCHA validation '''

			if result['success']:
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
				return redirect('home')
	else:
		form = MemberCreationForm()
	return render(request, 'registration/signup.html', {'form': form})

def account_activation_sent(request):
	return render(request, 'registration/account_activation_sent.html')

def activate(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None

	#If the user is already active, log them in and redirect to home
	if user.is_active:
		login(request, user)
		return redirect('home')

	if user is not None and account_activation_token.check_token(user, token):
		user.is_active = True
		user.member.email_confirmed = True
		user.save()
		login(request, user)
		return redirect('home')
	else:
		print(f'There was an error when {user} tried to activate')
		return render(request, 'registration/account_activation_invalid.html')

@login_required
def member_view(request, username):
	if not request.user.is_authenticated:
		return redirect('home')
	created_events = Event.objects.filter(creator=request.user, approved=True).order_by('start_date', 'start_time')
	pending_events = Event.objects.filter(creator=request.user, approved=False).order_by('start_date', 'start_time')
	created_calendars = Calendar.objects.filter(creator=request.user, approved=True).order_by('event_calendar')
	pending_calendars = Calendar.objects.filter(creator=request.user, approved=False).order_by('event_calendar')
	created_locations = Location.objects.filter(creator=request.user, approved=True).order_by('location')
	pending_locations = Location.objects.filter(creator=request.user, approved=False).order_by('location')
	return render(request, 'registration/member_view.html', {
		'created_events': created_events,
		'pending_events': pending_events,
		'created_calendars': created_calendars,
		'pending_calendars': pending_calendars,
		'created_locations': created_locations,
		'pending_locations': pending_locations,
	})

@login_required
def edit_member_info(request, username):
	if request.method == 'POST':
		form = MemberChangeForm(request.POST, instance=request.user)
		if form.is_valid():
			user = form.save(commit=False)
			if form.has_changed():
				if 'email' in form.changed_data:
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