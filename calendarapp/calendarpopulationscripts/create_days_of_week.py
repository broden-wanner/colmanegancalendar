from calendarapp.models import DayOfWeek

DayOfWeek.objects.create(day_of_week='Sunday', day_int=0)
DayOfWeek.objects.create(day_of_week='Monday', day_int=1)
DayOfWeek.objects.create(day_of_week='Tuesday', day_int=2)
DayOfWeek.objects.create(day_of_week='Wednesday', day_int=3)
DayOfWeek.objects.create(day_of_week='Thursday', day_int=4)
DayOfWeek.objects.create(day_of_week='Friday', day_int=5)
DayOfWeek.objects.create(day_of_week='Saturday', day_int=6)