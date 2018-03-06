from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import datetime

month_dictionary = {
	0: 'January',
	1: 'February',
	2: 'March',
	3: 'April',
	4: 'May',
	5: 'June',
	6: 'July',
	7: 'August',
	8: 'September',
	9: 'October',
	10: 'November',
	11: 'December',
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

	def save(self, *args, **kwargs):
		self.day_of_week_str = day_dictionary[self.day_of_week]
		super(Day, self).save(*args, **kwargs)

class Calendar(models.Model):
	event_calendar = models.CharField(max_length=100)

	def __str__(self):
		return f'{self.event_calendar} Calendar'

	def save(self, *args, **kwargs):
		self.event_calendar = self.event_calendar.title()
		super(Calendar, self).save(*args, **kwargs)

class Event(models.Model):
	title = models.CharField(max_length=100)
	event_info = models.TextField(blank=True)
	days = models.ManyToManyField('Day')
	start_time = models.DateTimeField()
	end_time = models.DateTimeField()
	calendar = models.ForeignKey('Calendar', on_delete=models.CASCADE)
	date_created = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.title

	def set_days_of_event(self):
		#Gets the first day of the event based on the start time
		first_day = Day.objects.get(
						month=Month.objects.get(
							year=Year.objects.get(year=self.start_time.year),
							month=self.start_time.month-1
						),
						day_of_month=self.start_time.day
					)
		#Time difference between dates
		delta = self.end_time - self.start_time
		#Add the first day to the days of the event
		self.days.add(first_day)
		#If the amount of days is greater than one
		if delta > datetime.timedelta(days=0):
			set_of_days = Day.objects.filter(id__gt=first_day.id, id__lte=first_day.id + delta.days)
			for day in set_of_days:
				self.days.add(day)

	def save(self, *args, **kwargs):
		self.title = self.title.title()
		self.date_created = timezone.now()
		super(Event, self).save(*args, **kwargs)
		self.set_days_of_event()