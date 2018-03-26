from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
from itertools import chain
import datetime

month_dictionary = {
	1: 'January',
	2: 'February',
	3: 'March',
	4: 'April',
	5: 'May',
	6: 'June',
	7: 'July',
	8: 'August',
	9: 'September',
	10: 'October',
	11: 'November',
	12: 'December',
}

day_dictionary = {
	0: 'Sunday',
	1: 'Monday',
	2: 'Tuesday',
	3: 'Wednesday',
	4: 'Thursday',
	5: 'Friday',
	6: 'Saturday',
}

class Year(models.Model):
	year = models.PositiveSmallIntegerField(default=0)
	start_day_of_year = models.PositiveSmallIntegerField(default=0)
	start_day_of_year_str = models.CharField(max_length=20, blank=True)
	days_in_year = models.PositiveSmallIntegerField(default=365)
	leap_year = models.BooleanField()

	def __str__(self):
		return str(self.year)

	def save(self, *args, **kwargs):
		self.start_day_of_year_str = day_dictionary[self.start_day_of_year]
		super(Year, self).save(*args, **kwargs)

class Month(models.Model):
	year = models.ForeignKey('Year', on_delete=models.CASCADE)
	month = models.PositiveSmallIntegerField(default=0)
	month_str = models.CharField(max_length=20, blank=True)
	days_in_month = models.PositiveSmallIntegerField(default=30)
	start_day_of_month = models.PositiveSmallIntegerField(default=0)
	start_day_of_month_str = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return '%s %i' % (self.month_str, int(self.year.year))

	def save(self, *args, **kwargs):
		self.month_str = month_dictionary[self.month]
		self.start_day_of_month_str = day_dictionary[self.start_day_of_month]
		super(Month, self).save(*args, **kwargs)

class Day(models.Model):
	month = models.ForeignKey('Month', on_delete=models.CASCADE)
	day_of_month = models.PositiveSmallIntegerField(default=1)
	day_of_week = models.PositiveSmallIntegerField(default=0)
	day_of_week_str = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return '%i of %s %i' % (self.day_of_month, self.month.month_str, int(self.month.year.year))

	def sorted_events(self):
		all_day_events = list(self.event_set.filter(all_day=True, approved=True))
		#Get events that last more than one day
		sorted_all_day_events = [event for event in all_day_events if event.end_date - event.start_date > datetime.timedelta(days=1)]
		#Sort them based on start date
		sorted_all_day_events.sort(key=lambda event: event.start_date)
		#Add the one-day all-day events at the end
		for event in all_day_events:
			if event not in sorted_all_day_events:
				sorted_all_day_events.append(event)

		timed_events = list(self.event_set.filter(all_day=False, approved=True).order_by('start_time'))
		#Get events that last more than one day
		sorted_timed_events = [event for event in timed_events if event.end_date - event.start_date > datetime.timedelta(days=1)]
		#Sort them based on start date
		sorted_timed_events.sort(key=lambda event: event.start_date)
		#Add events to the end if they are not multi-day
		for event in timed_events:
			if event not in sorted_timed_events:
				sorted_timed_events.append(event)

		#Puts all-day events before timed events
		return list(chain(sorted_all_day_events, sorted_timed_events))

	def save(self, *args, **kwargs):
		self.day_of_week_str = day_dictionary[self.day_of_week]
		super(Day, self).save(*args, **kwargs)

class Calendar(models.Model):
	event_calendar = models.CharField(max_length=100, unique=True)
	default_calendar = models.BooleanField(default=False)
	color = models.CharField(max_length=50, unique=True, null=True)
	slug = models.SlugField(unique=True, blank=True, null=True)

	def __str__(self):
		return f'{self.event_calendar} Calendar'

	def save(self, *args, **kwargs):
		self.event_calendar = self.event_calendar.title()
		self.slug = slugify(self.event_calendar)
		super(Calendar, self).save(*args, **kwargs)

class Location(models.Model):
	location = models.CharField(max_length=1000, unique=True)
	slug = models.SlugField(unique=True, blank=True)

	def __str__(self):
		return self.location

	def save(self, *args, **kwargs):
		self.location = self.location.title()
		self.slug = slugify(self.location)
		super(Location, self).save(*args, **kwargs)

class Member(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	calendar_preferences = models.ManyToManyField('Calendar', blank=True)
	email_confirmed = models.BooleanField(default=False)

	def __str__(self):
		return self.user.username

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Member.objects.create(user=instance)
        try:
        	instance.groups.add(Group.objects.get(name='Members'))
        except Group.DoesNotExist:
        	pass
    instance.member.save()

class DayOfWeek(models.Model):
	day_of_week = models.CharField(max_length=20)
	#Zero-indexed 0-6
	day_int = models.IntegerField(default=0)

	def __str__(self):
		return self.day_of_week

class Event(models.Model):
	title = models.CharField(max_length=100)
	approved = models.BooleanField(default=False)
	creator = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='creator')
	editor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='editor')
	event_info = models.TextField(blank=True)
	calendar = models.ForeignKey('Calendar', on_delete=models.CASCADE)
	location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)
	days = models.ManyToManyField('Day')
	start_date = models.DateField()
	start_time = models.TimeField()
	end_date = models.DateField()
	end_time = models.TimeField()
	all_day = models.BooleanField(default=False)
	date_created = models.DateTimeField(default=timezone.now)
	edited_time = models.DateTimeField(default=timezone.now)
	#Repeating fields
	repeat = models.BooleanField(default=False)
	repeat_every = models.PositiveIntegerField(default=1, blank=True, null=True)
	duration = models.CharField(
		max_length=1,
		blank=True,
		choices=(('1', 'Days'), ('2', 'Weeks'), ('3', 'Months'))
	)
	repeat_on = models.ManyToManyField('DayOfWeek', blank=True)
	ends_on = models.DateField(blank=True, null=True)
	ends_after = models.PositiveIntegerField(blank=True, null=True)
	slug = models.SlugField(unique=False, blank=True, null=True)

	def __str__(self):
		return self.title

	def set_days_of_event(self):
		#Gets the first day of the event based on the start time
		first_day = Day.objects.get(
						month=Month.objects.get(
							year=Year.objects.get(year=self.start_date.year),
							month=self.start_date.month
						),
						day_of_month=self.start_date.day
					)
		#Time difference between dates
		delta = self.end_date - self.start_date
		#Adds days based on date
		new_set_of_days = Day.objects.filter(id__gte=first_day.id, id__lte=first_day.id + delta.days)
		for day in new_set_of_days:
			self.days.add(day)

		#Handles recurrence
		recurring_days = []
		if self.repeat:
			#Skipping by days
			if self.duration == '1':
				#If set to end on a certain day
				if self.ends_on:
					recurring_days = Day.objects.filter(id__gte=first_day.id, id__lte=first_day.id + (self.ends_on - self.start_date).days)[self.repeat_every::self.repeat_every]
					for day in recurring_days:
						self.days.add(day)
				#If set to end after so many occurences
				elif self.ends_after:
					recurring_days = Day.objects.filter(id__gte=first_day.id, id__lte=first_day.id + (self.ends_after - 1)*self.repeat_every)[self.repeat_every::self.repeat_every]
					for day in recurring_days:
						self.days.add(day)
			#Skipping by weeks
			elif self.duration == '2':
				this_week = 0
				day_counter = 1
				#If set to end on a certain day
				if self.ends_on:
					temp_recurring_days = Day.objects.filter(id__gt=first_day.id, id__lte=first_day.id + (self.ends_on - self.start_date).days)
					for day in temp_recurring_days:
						for day_to_repeat_on in self.repeat_on.all():
							if day.day_of_week == day_to_repeat_on.day_int and this_week % self.repeat_every == 0:
								recurring_days.append(day)
								self.days.add(day)
						day_counter += 1
						if day_counter % 7 == 0:
							this_week += 1
						
				#If set to end after so many occurences
				elif self.ends_after:
					temp_recurring_days = Day.objects.filter(id__gt=first_day.id, id__lte=first_day.id + (self.ends_after - 1)*self.repeat_every*7 + (self.repeat_on.last().day_int - first_day.day_of_week))
					for day in temp_recurring_days:
						for day_to_repeat_on in self.repeat_on.all():
							if day.day_of_week == day_to_repeat_on.day_int and this_week % self.repeat_every == 0:
								recurring_days.append(day)
								self.days.add(day)
						day_counter += 1
						if day_counter % 7 == 0:
							this_week += 1
			#Skipping months
			elif self.duration == '3':
				#If set to end on a certain day
				if self.ends_on:
					recurring_days = Day.objects.filter(id__gte=first_day.id, id__lte=first_day.id + (self.ends_on - self.start_date).days, day_of_month=first_day.day_of_month)[self.repeat_every::self.repeat_every]
					for day in recurring_days:
						self.days.add(day)
				#If set to end after so many occurences
				if self.ends_after:
					recurring_days = Day.objects.filter(id__gte=first_day.id, day_of_month=first_day.day_of_month)[self.repeat_every::self.repeat_every]
					recurring_days = recurring_days[:self.ends_after-1]
					for day in recurring_days:
						self.days.add(day)

		#If change, removes days that were not in the new day set
		previous_day_set = self.days.all()
		for day in previous_day_set:
			if day not in list(chain(new_set_of_days, recurring_days)):
				self.days.remove(day)

	def clean(self):
		#Check to ensure the dates don't come before one another
		if datetime.datetime.combine(self.start_date, self.start_time) >= datetime.datetime.combine(self.end_date, self.end_time):
			raise ValidationError({
				'start_date': 'Start date must be less than or equal to end date.',
				'start_time': 'Start time must be less than end time.',
				'end_date': 'End date must be greater than or equal to start date.',
				'end_time': 'End time must be greater than start time.'
			})

		#Check recurring fields
		msg = 'If repeating event, must fill in this field'
		if self.repeat and not self.repeat_every:
			raise ValidationError({'repeat_every': msg})
		if self.repeat and not self.duration:
			raise ValidationError({'duration': msg})

		#If the event lasts more than 2 days and the user tries to repeat
		if self.repeat and self.end_date.day - self.start_date.day >= 1:
			raise ValidationError({'repeat': 'If repeating, event may only last one day.'})

		if self.repeat and not self.ends_on and not self.ends_after:
			raise ValidationError({'ends_on': 'Fill in either this field or the "Ends After" field'})
			raise ValidationError({'ends_after': 'Fill in either this field or the "Ends On" field'})
		if self.repeat and self.ends_on and self.ends_after:
			raise ValidationError({'ends_on': 'Fill in either this field or the "Ends After" field'})
			raise ValidationError({'ends_after': 'Fill in either this field or the "Ends On" field'})

		if self.repeat and self.ends_after:
			if self.ends_after <= 0:
				raise ValidationError({'ends_after': 'Must be a postive integer'})

		if self.repeat and self.repeat_every:
			if self.repeat_every <= 0:
				raise ValidationError({'repeat_every': 'Must be a postive integer'})

		if self.repeat and self.ends_on:
			if self.ends_on <= self.start_date:
				raise ValidationError({'ends_on': 'Must be later than the start date'})

	def save(self, *args, **kwargs):
		self.title = self.title.title()
		self.slug = slugify(self.title)
		self.full_clean()
		super(Event, self).save(*args, **kwargs)
		self.set_days_of_event()