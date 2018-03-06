from calendarapp.models import Year, Month

days_in_month = 31
#2010 began on Friday
start_day_of_month = 5

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