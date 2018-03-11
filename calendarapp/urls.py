from django.urls import path
from . import views

urlpatterns = [
	path('', views.calendarHomeView, name='home'),
	path('month/<int:year>/<int:month>/', views.calendarMonthView, name='month'),
	path('week/<int:year>/<int:month>/<int:first_day_of_week>/', views.calendarWeekView, name='week'),
	path('day/<int:year>/<int:month>/<int:day>/', views.calendarDayView, name='day'),
	path('event/new', views.newEventView, name='new_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/', views.calendarEventView, name='event_view'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/edit', views.editEventView, name='edit_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/delete', views.deleteEventView, name='delete_event'),
	path('calendar/new', views.newCalendarView, name='new_calendar'),
	path('calendar/<slug:slug>/', views.calendarView, name='calendar_view'),
	path('calendar/<slug:slug>/edit', views.editCalendarView, name='edit_calendar'),
	path('calendar/<slug:slug>/delete', views.deleteCalendarView, name='delete_calendar'),
	path('location/<slug:slug>/', views.locationView, name='location_view'),
]