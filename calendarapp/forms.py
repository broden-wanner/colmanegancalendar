from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.forms import ValidationError
from .models import Event, Calendar, DayOfWeek, Location

class EventForm(forms.ModelForm):
	title = forms.CharField(
		widget=forms.TextInput(attrs={'class': 'form-control'})
	)
	event_info = forms.CharField(
		widget=forms.Textarea(attrs={'class': 'form-control'}),
		required=False
	)
	calendar = forms.ModelChoiceField(
		queryset=Calendar.objects.filter(approved=True).order_by('event_calendar'),
		widget=forms.Select(attrs={'class': 'form-control'})
	)
	location = forms.ModelChoiceField(
		queryset=Location.objects.filter(approved=True).order_by('location'),
		required=False,
		widget=forms.Select(attrs={'class': 'form-control'})
	)
	start_date = forms.DateField(
		input_formats=['%m/%d/%Y'],
		widget=forms.DateInput(format='%m/%d/%Y', attrs={'class': 'form-control'})
	)
	start_time = forms.TimeField(
		input_formats=['%I:%M %p'],
		widget=forms.TimeInput(format='%I:%M %p', attrs={'class': 'form-control'})
	)
	end_date = forms.DateField(
		input_formats=['%m/%d/%Y'],
		widget=forms.DateInput(format='%m/%d/%Y', attrs={'class': 'form-control'})
	)
	end_time = forms.TimeField(
		input_formats=['%I:%M %p'],
		widget=forms.TimeInput(format='%I:%M %p', attrs={'class': 'form-control'})
	)
	#Handles data for the recurring aspect of the event
	repeat = forms.BooleanField(required=False)
	repeat_every = forms.IntegerField(
		widget=forms.NumberInput(attrs={'type': 'number', 'min': 1, 'class': 'form-control'}),
		required=False
	)
	repeat_on = forms.ModelMultipleChoiceField(
		queryset=DayOfWeek.objects.all(),
		widget=forms.CheckboxSelectMultiple(),
		required=False
	)
	ends_on = forms.DateField(
		input_formats=['%m/%d/%Y'],
		widget=forms.DateInput(format='%m/%d/%Y', attrs={'class': 'form-control'}),
	)
	ends_after = forms.IntegerField(
		widget=forms.NumberInput(attrs={'type': 'number', 'min': 1, 'class': 'form-control'}),
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
		widgets = {
			'duration': forms.Select(attrs={'class': 'form-control'}),
		}

	def clean(self):
		cleaned_data = super().clean()
		repeat = cleaned_data.get('repeat')
		duration = cleaned_data.get('duration')
		repeat_on = cleaned_data.get('repeat_on')

		#'2' corresponds to 'weeks' in the duration choice field
		if repeat and duration == '2' and not repeat_on:
			self.add_error('repeat_on', 'If repeating weekly, this field must be filled')

class ReasonForm(forms.Form):
	reason = forms.CharField(
		required=False,
		widget=forms.TextInput(attrs={'class': 'form-control'})
	)

	def __init__(self, *args, **kwargs):
		reason_label = kwargs.pop('label')
		super(ReasonForm, self).__init__(*args, **kwargs)
		self.fields['reason'].label = reason_label

class CalendarForm(forms.ModelForm):

	class Meta:
		model = Calendar
		fields = ('event_calendar', 'color', 'default_calendar')
		labels = {'event_calendar': 'Name:'}
		widgets = {
			'event_calendar': forms.TextInput(attrs={'class': 'form-control'}),
		}

class LocationForm(forms.ModelForm):

	class Meta:
		model = Location
		fields = ('location',)
		widgets = {'location': forms.TextInput(attrs={'class': 'form-control'})}
		labels = {'location': 'Location name:'}

class MemberCreationForm(UserCreationForm):
	first_name = forms.CharField(
		max_length=30,
		widget=forms.TextInput(attrs={'class': 'form-control'})
	)
	last_name = forms.CharField(
		max_length=30,
		widget=forms.TextInput(attrs={'class': 'form-control'})
	)
	email = forms.EmailField(
		max_length=254,
		help_text='Required. Input a valid email address.',
		required=True,
		widget=forms.EmailInput(attrs={'class': 'form-control'})
	)
	calendar_preferences = forms.ModelMultipleChoiceField(
		queryset=Calendar.objects.filter(approved=True).order_by('event_calendar'),
		widget=forms.CheckboxSelectMultiple(),
		required=False
	)
	password1 = forms.CharField(
		widget=forms.PasswordInput(attrs={'class': 'form-control'}),
		required=True,
		label='Password',
		help_text="<ul><li>Your password can't be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can't be a commonly used password.</li><li>Your password can't be entirely numeric.</li></ul>"
	)
	password2 = forms.CharField(
		widget=forms.PasswordInput(attrs={'class': 'form-control'}),
		required=True,
		label='Password Confirmation',
		help_text='Enter the same password as before, for verification.'
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
		widgets = {
			'username': forms.TextInput(attrs={'class': 'form-control'}),
		}

	def clean_email(self):
		email = self.cleaned_data.get('email')
		username = self.cleaned_data.get('username')
		if User.objects.filter(email=email).exclude(username=username).exists():
			self.add_error('email', 'There is already another account with this email. If you forgot your password, use the lost password form on the login page.')
		return email

class MemberChangeForm(forms.ModelForm):
	username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
	calendar_preferences = forms.ModelMultipleChoiceField(
		queryset=Calendar.objects.filter(approved=True).order_by('event_calendar'),
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
		widgets = {
			'first_name': forms.TextInput(attrs={'class': 'form-control'}),
			'last_name': forms.TextInput(attrs={'class': 'form-control'}),
			'email': forms.EmailInput(attrs={'class': 'form-control'}),
		}

	def clean_email(self):
		email = self.cleaned_data.get('email')
		username = self.cleaned_data.get('username')
		if User.objects.exclude(username=username).filter(email=email).exists():
			self.add_error('email', 'There is already another account with this email. If you forgot your password, use the lost password form on the login page.')
		return email