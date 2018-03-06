from calendarapp.models import Year, Month, Day

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
	print("Finished year %i" % (year.year))