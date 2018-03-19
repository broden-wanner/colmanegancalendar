from django.urls import path
from . import views

urlpatterns = [
	path('', views.calendarHomeView, name='home'),
	path('month/<int:year>/<int:month>/', views.calendarMonthView, name='month'),
	path('week/<int:year>/<int:month>/<int:first_day_of_week>/', views.calendarWeekView, name='week'),
	path('day/<int:year>/<int:month>/<int:day>/', views.calendarDayView, name='day'),
	path('event/new/', views.newEventView, name='new_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/', views.calendarEventView, name='event_view'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/edit/', views.editEventView, name='edit_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/delete/', views.deleteEventView, name='delete_event'),
	path('event/<int:pk>/<slug:slug>/approve/', views.approve_event, name='approve_event'),
	path('event/<int:pk>/<slug:slug>/approval-sent/', views.event_approval_sent, name='event_approval_sent'),
	path('calendar/new/', views.newCalendarView, name='new_calendar'),
	path('calendar/<slug:slug>/', views.calendarView, name='calendar_view'),
	path('calendar/<slug:slug>/edit/', views.editCalendarView, name='edit_calendar'),
	path('calendar/<slug:slug>/delete/', views.deleteCalendarView, name='delete_calendar'),
	path('location/<slug:slug>/', views.locationView, name='location_view'),
	path('accounts/signup/', views.signup, name='signup'),
	path('accounts/<str:username>/view/', views.member_view, name='member_view'),
	path('accounts/account-activation-sent/', views.account_activation_sent, name='account_activation_sent'),
	path('accounts/activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
	path('accounts/<str:username>/edit/', views.edit_member_info, name='edit_member_info'),
	path('accounts/account-email-change-sent/', views.account_email_change_sent, name='account_email_change_sent'),
]