from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.forms import ValidationError
from .models import Event, Calendar, DayOfWeek, Location

class EventForm(forms.ModelForm):
	calendar = forms.ModelChoiceField(
		queryset=Calendar.objects.all().order_by('event_calendar')
	)
	location = forms.ModelChoiceField(
		queryset=Location.objects.all().order_by('location'),
		required=False
	)
	start_date = forms.DateField(
		input_formats=['%m/%d/%Y'],
		widget=forms.DateInput(format='%m/%d/%Y')
	)
	start_time = forms.TimeField(
		input_formats=['%I:%M %p'],
		widget=forms.TimeInput(format='%I:%M %p')
	)
	end_date = forms.DateField(
		input_formats=['%m/%d/%Y'],
		widget=forms.DateInput(format='%m/%d/%Y')
	)
	end_time = forms.TimeField(
		input_formats=['%I:%M %p'],
		widget=forms.TimeInput(format='%I:%M %p')
	)
	#Handles data for the recurring aspect of the event
	repeat = forms.BooleanField(required=False)
	repeat_every = forms.IntegerField(
		widget=forms.NumberInput(attrs={'type': 'number', 'min': 1}),
		required=False
	)
	repeat_on = forms.ModelMultipleChoiceField(
		queryset=DayOfWeek.objects.all(),
		widget=forms.CheckboxSelectMultiple(),
		required=False
	)
	ends_on = forms.DateField(
		input_formats=['%Y-%m-%d'],
		widget=forms.DateInput(attrs={'type': 'date'}),
		required=False
	)
	ends_after = forms.IntegerField(
		widget=forms.NumberInput(attrs={'type': 'number', 'min': 1}),
		required=False,
		help_text='occurences'
	)
	
	class Meta:
		model = Event
		fields = (
			'title',
			'event_info',
			'location',
			'calendar',
			'start_date',
			'start_time',
			'end_date',
			'end_time',
			'all_day',
			'repeat',
			'repeat_every',
			'duration',
			'repeat_on',
			'ends_on',
			'ends_after'
		)

	def clean(self):
		cleaned_data = super().clean()
		repeat = cleaned_data.get('repeat')
		duration = cleaned_data.get('duration')
		repeat_on = cleaned_data.get('repeat_on')

		#'2' corresponds to 'weeks' in the duration choice field
		if repeat and duration == '2' and not repeat_on:
			self.add_error('repeat_on', 'If repeating weekly, this field must be filled')

class CalendarForm(forms.ModelForm):

	class Meta:
		model = Calendar
		fields = ('event_calendar', 'color', 'default_calendar')

class MemberCreationForm(UserCreationForm):
	first_name = forms.CharField(max_length=30)
	last_name = forms.CharField(max_length=30)
	email = forms.EmailField(max_length=254, help_text='Required. Input a valid email address.', required=True)
	calendar_preferences = forms.ModelMultipleChoiceField(
		queryset=Calendar.objects.all().order_by('event_calendar'),
		widget=forms.CheckboxSelectMultiple(),
		required=False
	)

	class Meta:
		model = User
		fields = (
			'username',
			'first_name',
			'last_name',
			'email',
			'password1',
			'password2',
			'calendar_preferences'
		)

	def clean_email(self):
		email = self.cleaned_data.get('email')
		username = self.cleaned_data.get('username')
		if User.objects.filter(email=email).exclude(username=username).exists():
			self.add_error('email', 'There is already another account with this email. If you forgot your password, use the lost password form on the login page.')
		return email

class MemberChangeForm(forms.ModelForm):
	username = forms.CharField()
	calendar_preferences = forms.ModelMultipleChoiceField(
		queryset=Calendar.objects.all().order_by('event_calendar'),
		widget=forms.CheckboxSelectMultiple(),
		required=False
	)

	class Meta:
		model = User
		fields = (
			'username',
			'first_name',
			'last_name',
			'email',
			'calendar_preferences',
		)

	def clean_email(self):
		email = self.cleaned_data.get('email')
		username = self.cleaned_data.get('username')
		if User.objects.exclude(username=username).filter(email=email).exists():
			self.add_error('email', 'There is already another account with this email. If you forgot your password, use the lost password form on the login page.')
		return email