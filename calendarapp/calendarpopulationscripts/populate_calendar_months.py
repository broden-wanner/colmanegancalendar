from calendarapp.models import Year, Month

days_in_month = 31
#2010 began on Friday
start_day_of_month = 5

for year in Year.objects.all():
	for m in range(1, 13):
		#Handles days in month
		if m in [1, 3, 5, 7, 8, 10, 12]:
			days_in_month = 31
		elif m in [4, 6, 9, 11]:
			days_in_month = 30
		elif m == 2 and year.leap_year:
			days_in_month = 29
		elif m == 2 and year.leap_year == False:
			days_in_month = 28

		calendar_month = Month(year=year, month=m, days_in_month=days_in_month, start_day_of_month=start_day_of_month)
		calendar_month.save()

		#Handles start days
		if m in [1, 3, 5, 7, 8, 10, 12]:
			start_day_of_month += 3
		elif m in [4, 6, 9, 11]:
			start_day_of_month += 2
		elif m == 2 and year.leap_year:
			start_day_of_month += 1

		if start_day_of_month > 6:
			start_day_of_month -= 7