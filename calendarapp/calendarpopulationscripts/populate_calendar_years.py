from calendarapp.models import Year

#2010 began on a monday
start_day_of_year = 5
leap_year = False

for y in range(2010, 2030):
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

