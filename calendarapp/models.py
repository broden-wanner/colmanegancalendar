from django.db import models
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
		#Sort events with all day ones coming first (ordered by title) then other events (ordered by time)
		return list(chain(self.event_set.filter(all_day=True).order_by('title'), self.event_set.exclude(all_day=True).order_by('start_time')))

	def save(self, *args, **kwargs):
		self.day_of_week_str = day_dictionary[self.day_of_week]
		super(Day, self).save(*args, **kwargs)

class Calendar(models.Model):
	event_calendar = models.CharField(max_length=100, unique=True)
	#creator = models.ForeignKey('auth.User', on_delete=models.CASCADE)
	slug = models.SlugField(unique=True, blank=True, null=True)

	def __str__(self):
		return f'{self.event_calendar} Calendar'

	def save(self, *args, **kwargs):
		self.event_calendar = self.event_calendar.title()
		self.slug = slugify(self.event_calendar)
		super(Calendar, self).save(*args, **kwargs)

class Location(models.Model):
	location = models.CharField(max_length=1000, unique=True)
	#creator = models.ForeignKey('auth.User', on_delete=models.CASCADE)
	slug = models.SlugField(unique=True, blank=True)

	def __str__(self):
		return self.location

	def save(self, *args, **kwargs):
		self.location = self.location.title()
		self.slug = slugify(self.location)
		super(Location, self).save(*args, **kwargs)

class Event(models.Model):
	title = models.CharField(max_length=100)
	#creator = models.ForeignKey('auth.User', on_delete=models.CASCADE)
	slug = models.SlugField(unique=False, blank=True, null=True)
	event_info = models.TextField(blank=True)
	location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True)
	days = models.ManyToManyField('Day')
	start_date = models.DateField()
	start_time = models.TimeField()
	end_date = models.DateField()
	end_time = models.TimeField()
	all_day = models.BooleanField(default=False)
	calendar = models.ForeignKey('Calendar', on_delete=models.CASCADE)
	date_created = models.DateTimeField(default=timezone.now)

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
		#Add the first day to the days of the event
		self.days.add(first_day)
		#If the amount of days is greater than one
		if delta > datetime.timedelta(days=0):
			set_of_days = Day.objects.filter(id__gt=first_day.id, id__lte=first_day.id + delta.days)
			for day in set_of_days:
				self.days.add(day)

	def clean(self):
		if self.start_date > self.end_date:
			raise ValidationError({
				'start_date': 'Start date must be less than or equal to end date.',
				'end_date': 'End date must be greater than or equal to start date.'
			})
		if self.start_time >= self.end_time:
			raise ValidationError({
				'start_time':'Start time must be less than end time.',
				'end_time': 'End time must be greater than start time.'
			})

	def save(self, *args, **kwargs):
		self.title = self.title.title()
		self.slug = slugify(self.title)
		self.date_created = timezone.now()
		self.full_clean()
		super(Event, self).save(*args, **kwargs)
		self.set_days_of_event()