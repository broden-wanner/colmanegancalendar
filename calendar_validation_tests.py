import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_base.settings')
django.setup()

import unittest
from calendarapp import models
from calendarapp.models import Year, Month, Day


class CalendarTest(unittest.TestCase):

	def year_tester(self, year_object, year, start_day, start_day_str, days_in_year, leap_year):
		self.assertEquals(year_object.year, year, f'The year is wrong for {year_object.year}')
		self.assertEquals(year_object.start_day_of_year, start_day, f'The year {year_object.year} does not start on {year_object.start_day_of_year}')
		self.assertEquals(year_object.start_day_of_year_str, start_day_str, f'The year {year_object.year} does not start on {year_object.start_day_of_year_str}')
		self.assertEquals(year_object.days_in_year, days_in_year, f'The year {year_object.year} does not have {year_object.days_in_year} days in it')
		self.assertEquals(year_object.leap_year, leap_year, f'The year {year_object.year} has wrong leap year designation')

	def test_years_count(self):
		for y in range(2010, 2030):
			self.assertEquals(Year.objects.filter(year=y).count(), 1)

	def test_year_validity(self):
		self.year_tester(Year.objects.get(year=2010), 2010, 5, 'Friday', 365, False)
		self.year_tester(Year.objects.get(year=2012), 2012, 0, 'Sunday', 366, True)
		self.year_tester(Year.objects.get(year=2017), 2017, 0, 'Sunday', 365, False)	
		self.year_tester(Year.objects.get(year=2018), 2018, 1, 'Monday', 365, False)

	def month_tester(self, month_object, year, month, month_str, days_in_month, start_day_of_month, start_day_of_month_str):
		self.assertEquals(month_object.year, year, 'Something wrong with the year of')
		self.assertEquals(month_object.month, month, 'Something wrong with month of')
		self.assertEquals(month_object.month_str, month_str, 'Something wrong with month_str of')
		self.assertEquals(month_object.days_in_month, days_in_month, 'Wrong days of month in')
		self.assertEquals(month_object.start_day_of_month, start_day_of_month, 'Wrong start day of month')
		self.assertEquals(month_object.start_day_of_month_str, start_day_of_month_str, 'Wrong start day of month string')

	def test_to_ensure_all_months_exist(self):
		for year in Year.objects.all():
			self.assertEquals(Month.objects.filter(year=year).count(), 12)

	def test_month_validity(self):
		year = Year.objects.get(year=2010)
		self.month_tester(Month.objects.get(year=year, month=0), year, 0, 'January', 31, 5, 'Friday')
		self.month_tester(Month.objects.get(year=year, month=1), year, 1, 'February', 28, 1, 'Monday')
		self.month_tester(Month.objects.get(year=year, month=6), year, 6, 'July', 31, 4, 'Thursday')
		self.month_tester(Month.objects.get(year=year, month=11), year, 11, 'December', 31, 3, 'Wednesday')
		year = Year.objects.get(year=2016)
		self.month_tester(Month.objects.get(year=year, month=0), year, 0, 'January', 31, 5, 'Friday')
		self.month_tester(Month.objects.get(year=year, month=1), year, 1, 'February', 29, 1, 'Monday')
		self.month_tester(Month.objects.get(year=year, month=6), year, 6, 'July', 31, 5, 'Friday')
		self.month_tester(Month.objects.get(year=year, month=11), year, 11, 'December', 31, 4, 'Thursday')
		year = Year.objects.get(year=2020)
		self.month_tester(Month.objects.get(year=year, month=0), year, 0, 'January', 31, 3, 'Wednesday')
		self.month_tester(Month.objects.get(year=year, month=1), year, 1, 'February', 29, 6, 'Saturday')
		self.month_tester(Month.objects.get(year=year, month=6), year, 6, 'July', 31, 3, 'Wednesday')
		self.month_tester(Month.objects.get(year=year, month=11), year, 11, 'December', 31, 2, 'Tuesday')

	def day_tester(self, day_object, month, day_of_month, day_of_week, day_of_week_str):
		self.assertEquals(day_object.month, month, 'Wrong month on this day')
		self.assertEquals(day_object.day_of_month, day_of_month, 'Wrong day of month')
		self.assertEquals(day_object.day_of_week, day_of_week, 'Wrong day of week')
		self.assertEquals(day_object.day_of_week_str, day_of_week_str, 'Wrong day of week string')

	def test_day_validity(self):
		month = Month.objects.get(year=Year.objects.get(year=2011), month=0)
		self.day_tester(Day.objects.get(month=month, day_of_month=1), month, 1, 6, 'Saturday')

		month = Month.objects.get(year=Year.objects.get(year=2011), month=1)
		self.day_tester(Day.objects.get(month=month, day_of_month=28), month, 28, 1, 'Monday')

		month = Month.objects.get(year=Year.objects.get(year=2011), month=10)
		self.day_tester(Day.objects.get(month=month, day_of_month=25), month, 25, 5, 'Friday')

		month = Month.objects.get(year=Year.objects.get(year=2017), month=0)
		self.day_tester(Day.objects.get(month=month, day_of_month=28), month, 28, 6, 'Saturday')

		month = Month.objects.get(year=Year.objects.get(year=2017), month=4)
		self.day_tester(Day.objects.get(month=month, day_of_month=22), month, 22, 1, 'Monday')

		month = Month.objects.get(year=Year.objects.get(year=2018), month=0)
		self.day_tester(Day.objects.get(month=month, day_of_month=1), month, 1, 1, 'Monday')

		month = Month.objects.get(year=Year.objects.get(year=2018), month=10)
		self.day_tester(Day.objects.get(month=month, day_of_month=23), month, 23, 5, 'Friday')

	def test_to_ensure_all_days_exist_in_months(self):
		for month in Month.objects.all():
			try:
				self.assertEquals(Day.objects.filter(month=month).count(), month.days_in_month)
			except (AssertionError):
				print(f'Missing days in {month.month_str} {month.year.year}')

if __name__ == '__main__':  
	unittest.main(warnings='ignore')