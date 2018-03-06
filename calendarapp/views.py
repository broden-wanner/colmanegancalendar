from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.utils import timezone
from .models import Year, Month, Day, Calendar, Event
from .forms import NewEventForm

def calendarHomeView(request):
	year = int(timezone.now().year)
	month = int(timezone.now().month-1)
	return redirect('month', year=year, month=month)

def calendarMonthView(request, year, month):
	current_year = get_object_or_404(Year, year=year)
	current_month = get_object_or_404(Month, year=current_year, month=month)		
	days_of_month = get_list_or_404(Day, month=current_month)

	number_of_days_from_previous_month = days_of_month[0].day_of_week
	number_of_days_from_next_month = 6 - days_of_month[-1].day_of_week + 7

	if month > 0:
		previous_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year), month=month-1)
		previous_month_days = Day.objects.filter(month=previous_month).order_by('day_of_month').reverse()[0:number_of_days_from_previous_month]
	elif month == 0:
		previous_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year-1), month=11)
		previous_month_days = Day.objects.filter(month=previous_month).order_by('day_of_month').reverse()[0:number_of_days_from_previous_month]
	previous_month_days = list(previous_month_days)[::-1]

	if month < 11:
		next_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year), month=month+1)
		next_month_days = Day.objects.filter(month=next_month)[0:number_of_days_from_next_month]
	elif month == 11:
		next_month = get_object_or_404(Month, year=get_object_or_404(Year, year=year+1), month=0)
		next_month_days = Day.objects.filter(month=next_month)[0:number_of_days_from_next_month]

	calendar_rows = []
	day_index = 0
	next_day_index = 0
	for i in range(6):
		week_row = []
		if i == 0:
			for day in previous_month_days:
				week_row.append(day)
			for j in range(7 - len(previous_month_days)):
				week_row.append(days_of_month[day_index])
				day_index += 1
		elif i > 0 and i < 4:
			for j in range(7):
				week_row.append(days_of_month[day_index])
				day_index += 1
		elif i == 4 or i == 5:
			for j in range(7):
				if day_index < len(days_of_month):
					week_row.append(days_of_month[day_index])
					day_index += 1
				elif next_day_index < len(next_month_days):
					week_row.append(next_month_days[next_day_index])
					next_day_index += 1
		calendar_rows.append(week_row)

	return render(request, 'month.html', {
		'month_weeks': calendar_rows,
		'current_month': current_month,
		'next_month': next_month,
		'previous_month': previous_month,
	})

def newEventView(request):
	if request.method == 'POST':
		new_event_form = NewEventForm(request.POST)
		if new_event_form.is_valid():
			new_event = new_event_form.save(commit=False)
			new_event.save()
			return redirect('month', year=new_event.start_time.year, month=new_event.start_time.month-1)
	else:
		new_event_form = NewEventForm()

	return render(request, 'new_event.html', {'new_event_form': new_event_form})