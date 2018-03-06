from django.test import TestCase
from django.utils import timezone
import datetime
from .models import Calendar, Event, Year, Month, Day

#Creates test years from 2017 to end_year
def create_test_years(end_year):
	#2017 began on a Sunday
	start_day_of_year = 0
	leap_year = False

	for y in range(2017, end_year):
		#If the year is divisible by 4, it is a leap year
		#1900 and 2100 are not leap years for some reason
		if y % 4 == 0 and y != 1900 and y != 2100:
			days_in_year = 366
			leap_year = True
		else:
			days_in_year = 365
			leap_year = False

		calendar_year = Year(year=y, start_day_of_year=start_day_of_year, days_in_year=days_in_year, leap_year=leap_year)
		calendar_year.save()

		#If the year is a leap year, then the start date goes forward two days
		if y % 4 == 0 and y != 1900 and y != 2100:
			start_day_of_year += 2
		else:
			start_day_of_year += 1

		#Handles the looping of the start day
		if start_day_of_year == 7:
			start_day_of_year = 0
		#Hanles looping of start day if leap year
		elif start_day_of_year == 8:
			start_day_of_year = 1

	days_in_month = 31
	#2017 began on a Sunday
	start_day_of_month = 0

	for year in Year.objects.all():
		for m in range(12):
			#Handles days in month
			if m in [0, 2, 4, 6, 7, 9, 11]:
				days_in_month = 31
			elif m in [3, 5, 8, 10]:
				days_in_month = 30
			elif m == 1 and year.leap_year:
				days_in_month = 29
			elif m == 1 and year.leap_year == False:
				days_in_month = 28

			calendar_month = Month(year=year, month=m, days_in_month=days_in_month, start_day_of_month=start_day_of_month)
			calendar_month.save()

			#Handles start days
			if m in [0, 2, 4, 6, 7, 9, 11]:
				start_day_of_month += 3
			elif m in [3, 5, 8, 10]:
				start_day_of_month += 2
			elif m == 1 and year.leap_year:
				start_day_of_month += 1

			if start_day_of_month > 6:
				start_day_of_month -= 7

	day_of_week = 0

	for year in Year.objects.all():
		for month in Month.objects.filter(year=year):
			for d in range(1, month.days_in_month + 1):
				if d == 1:
					day_of_week = month.start_day_of_month
				else:
					day_of_week += 1

				if day_of_week > 6:
					day_of_week -= 7

				calendar_day = Day(month=month, day_of_month=d, day_of_week=day_of_week)
				calendar_day.save()

class AppTests(TestCase):
	@classmethod
	def setUpTestData(self):
		create_test_years(2019)

	##
	## Home Page View Tests
	##

	def test_redirect_to_current_month(self):
		response = self.client.get('/')
		self.assertRedirects(response, f'/month/{timezone.now().year}/{timezone.now().month-1}/')

	##
	## Month View Tests
	##

	def test_uses_month_template(self):
		response = self.client.get(f'/month/{timezone.now().year}/{timezone.now().month-1}/')
		self.assertTemplateUsed(response, 'month.html')
		self.assertTemplateUsed(response, 'base.html')

	def test_displays_month_correctly(self):
		response = self.client.get(f'/month/2018/6/')
		self.assertContains(response, 'July 2018')
		self.assertContains(response, '1st of July')
		self.assertContains(response, '1st of August')

	def test_passes_correct_months_into_template(self):
		month = Month.objects.get(year=Year.objects.get(year=2018), month=6)
		next_month = Month.objects.get(year=Year.objects.get(year=2018), month=7)
		previous_month = Month.objects.get(year=Year.objects.get(year=2018), month=5)
		response = self.client.get(f'/month/{month.year.year}/{month.month}/')
		self.assertEquals(response.context['current_month'], month)
		self.assertEquals(response.context['next_month'], next_month)
		self.assertEquals(response.context['previous_month'], previous_month)

	def test_event_appears_on_month_calendar(self):
		calendar = Calendar(event_calendar='Random calendar')
		calendar.save()

		start_time = datetime.datetime(2018, 1, 1, 4, 0, tzinfo=timezone.get_current_timezone())
		end_time = datetime.datetime(2018, 1, 1, 6, 52, tzinfo=timezone.get_current_timezone())

		event = Event(
			title = 'event 1',
			start_time = start_time,
			end_time = end_time,
			calendar = calendar
		)
		event.save()

		response = self.client.get(f'/month/{start_time.year}/{start_time.month-1}/')
		self.assertContains(response, 'Event 1')

	def test_event_spanning_more_than_one_day_appears_under_all_days(self):
		calendar = Calendar(event_calendar='Random calendar')
		calendar.save()

		start_time = datetime.datetime(2018, 1, 1, 4, 0, tzinfo=timezone.get_current_timezone())
		end_time = datetime.datetime(2018, 1, 3, 6, 52, tzinfo=timezone.get_current_timezone())

		event = Event(
			title = 'event 1',
			start_time = start_time,
			end_time = end_time,
			calendar = calendar
		)
		event.save()

		response = self.client.get(f'/month/{start_time.year}/{start_time.month-1}/')
		self.assertContains(response, 'Event 1', 3)

	def test_returns_404_for_month_not_in_database(self):
		response = self.client.get(f'/month/22/2020/')
		self.assertEquals(response.status_code, 404)
		response = self.client.get(f'/month/8/2030/')
		self.assertEquals(response.status_code, 404)

	##
	## Calendar and Event Testers
	##

	def test_creating_calendar(self):
		calendar = Calendar(event_calendar='Random calendar')
		calendar.save()

		self.assertEquals(Calendar.objects.count(), 1)

		saved_calendar = Calendar.objects.first()
		self.assertEquals(calendar, saved_calendar)
		self.assertEquals(saved_calendar.event_calendar, 'Random Calendar')

	def test_creating_single_event_under_calendar(self):
		calendar = Calendar(event_calendar='Random calendar')
		calendar.save()

		start_time = datetime.datetime(2018, 1, 1, 4, 0, tzinfo=timezone.get_current_timezone())
		end_time = datetime.datetime(2018, 1, 1, 6, 52, tzinfo=timezone.get_current_timezone())

		event = Event(
			title = 'event 1',
			start_time = start_time,
			end_time = end_time,
			calendar = calendar
		)
		event.save()

		self.assertEquals(Event.objects.count(), 1)
		saved_event = Event.objects.first()
		self.assertEquals(event, saved_event)
		self.assertEquals(saved_event.title, 'Event 1')
		self.assertEquals(saved_event.days.count(), 1)
		self.assertEquals(saved_event.days.first().day_of_month, start_time.day)
		self.assertEquals(saved_event.days.first().month.month, start_time.month-1)
		self.assertEquals(saved_event.start_time, start_time)
		self.assertEquals(saved_event.end_time, end_time)
		self.assertEquals(saved_event.calendar, calendar)

	def test_creating_event_that_spans_more_than_one_day(self):
		calendar = Calendar(event_calendar='Random calendar')
		calendar.save()

		start_time = datetime.datetime(2017, 1, 1, 4, 0, tzinfo=timezone.get_current_timezone())
		end_time = datetime.datetime(2017, 1, 4, 6, 52, tzinfo=timezone.get_current_timezone())

		event = Event(
			title = 'event 1',
			start_time = start_time,
			end_time = end_time,
			calendar = calendar
		)
		event.save()
		#event.set_days_of_event()

		self.assertEquals(Event.objects.count(), 1)
		saved_event = Event.objects.first()
		self.assertEquals(event, saved_event)
		self.assertEquals(saved_event.title, 'Event 1')
		self.assertEquals(saved_event.days.count(), 4)
		self.assertEquals(saved_event.days.first().day_of_month, start_time.day)
		self.assertEquals(saved_event.days.first().month.month, start_time.month-1)
		self.assertEquals(saved_event.days.last().day_of_month, end_time.day)
		self.assertEquals(saved_event.days.last().month.month, end_time.month-1)
		self.assertEquals(saved_event.start_time, start_time)
		self.assertEquals(saved_event.end_time, end_time)
		self.assertEquals(saved_event.calendar, calendar)