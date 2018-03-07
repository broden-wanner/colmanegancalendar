from django import forms
from .models import Event, Calendar

class EventForm(forms.ModelForm):
	start_date = forms.DateField(
		input_formats=['%Y-%m-%d'],
		widget=forms.DateInput(attrs={'type': 'date'})
	)
	start_time = forms.TimeField(
		input_formats=['%H:%M'],
		widget=forms.TimeInput(attrs={'type': 'time'})
	)
	end_date = forms.DateField(
		input_formats=['%Y-%m-%d'],
		widget=forms.DateInput(attrs={'type': 'date'})
	)
	end_time = forms.TimeField(
		input_formats=['%H:%M'],
		widget=forms.TimeInput(attrs={'type': 'time'})
	)
	class Meta:
		model = Event
		fields = ['title', 'event_info', 'calendar', 'start_date', 'start_time', 'end_date', 'end_time', 'all_day']

class CalendarForm(forms.ModelForm):

	class Meta:
		model = Calendar
		fields = ['event_calendar']