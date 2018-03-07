from django.urls import path
from . import views

urlpatterns = [
	path('', views.calendarHomeView, name='home'),
	path('event/new', views.newEventView, name='new_event'),
	path('calendar/new', views.newCalendarView, name='new_calendar'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/', views.calendarEventView, name='event_view'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/edit', views.editEventView, name='edit_event'),
	path('month/<int:year>/<int:month>/', views.calendarMonthView, name='month'),
]