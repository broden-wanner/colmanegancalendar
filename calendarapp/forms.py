from django import forms
from django.forms import ValidationError
from .models import Event, Calendar

class EventForm(forms.ModelForm):
	start_date = forms.DateField(
		input_formats=['%Y-%m-%d'],
		widget=forms.DateInput(attrs={'type': 'date'})
	)
	start_time = forms.TimeField(
		input_formats=['%H:%M'],
		widget=forms.TimeInput(attrs={'type': 'time'}, format='%H:%M')
	)
	end_date = forms.DateField(
		input_formats=['%Y-%m-%d'],
		widget=forms.DateInput(attrs={'type': 'date'})
	)
	end_time = forms.TimeField(
		input_formats=['%H:%M'],
		widget=forms.TimeInput(attrs={'type': 'time'}, format='%H:%M')
	)
	#Handles data for the recurring aspect of the event
	repeat = forms.BooleanField(required=False)
	repeat_every = forms.IntegerField(
		widget=forms.NumberInput(attrs={'type': 'number', 'min': 1}),
		required=False
	)
	duration = forms.ChoiceField(
		choices=[('1', 'Days'), ('2', 'Weeks'), ('3', 'Months')],
		widget=forms.RadioSelect(),
		required=False
	)
	repeat_on = forms.MultipleChoiceField(
		choices=[('0', 'Sun'), ('1', 'Mon'), ('2', 'Tue'), ('3', 'Wed'), ('4', 'Thu'), ('5', 'Fri'), ('6', 'Sat')],
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
		required=False
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
		)

	def clean(self):
		cleaned_data = super().clean()
		repeating_fields = ['repeat', 'repeat_every', 'duration', 'repeat_on']

		repeating_fields_cleaned_data = []
		for field in repeating_fields:
			repeating_fields_cleaned_data.append(cleaned_data.get(field))

		msg = 'If repeating event, must fill in this field'
		for i in range(1, len(repeating_fields)):
			if repeating_fields_cleaned_data[0] and not repeating_fields_cleaned_data[i]:
				self.add_error(repeating_fields[i], msg)

		ends_on = cleaned_data.get('ends_on')
		ends_after = cleaned_data.get('ends_after')
		if repeating_fields_cleaned_data[0] and not ends_on and not ends_after:
			self.add_error('ends_on', 'Fill in either this field or the "Ends After" field')
			self.add_error('ends_after', 'Fill in either this field or the "Ends On" field')
		if repeating_fields_cleaned_data[0] and ends_on and ends_after:
			self.add_error('ends_on', 'Fill in either this field or the "Ends After" field')
			self.add_error('ends_after', 'Fill in either this field or the "Ends On" field')

		if ends_after:
			if ends_after <= 0:
				self.add_error('ends_after', 'Must be a postive integer')

		if repeating_fields_cleaned_data[1]:
			if repeating_fields_cleaned_data[1] <= 0:
				self.add_error(repeating_fields[1], 'Must be a postive integer')

class CalendarForm(forms.ModelForm):

	class Meta:
		model = Calendar
		fields = ('event_calendar',)