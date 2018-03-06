from django import forms
from .models import Event, Calendar

class NewEventForm(forms.ModelForm):
	start_time = forms.DateTimeField(
		input_formats=['%Y-%m-%dT%H:%M'],
		widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
	)
	end_time = forms.DateTimeField(
		input_formats=['%Y-%m-%dT%H:%M'],
		widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
	)
	class Meta:
		model = Event
		fields = ['title', 'event_info', 'calendar', 'start_time', 'end_time']