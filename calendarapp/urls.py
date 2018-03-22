from django.urls import path
from . import calendar_views
from . import event_views
from . import event_calendar_views
from . import account_views
from . import location_views

#Calendar views
urlpatterns = [
	path('', calendar_views.calendarHomeView, name='home'),
	path('month/<int:year>/<int:month>/', calendar_views.calendarMonthView, name='month'),
	path('week/<int:year>/<int:month>/<int:first_day_of_week>/', calendar_views.calendarWeekView, name='week'),
	path('day/<int:year>/<int:month>/<int:day>/', calendar_views.calendarDayView, name='day'),
]

#Event Views
urlpatterns += [
	path('event/new/', event_views.newEventView, name='new_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/', event_views.calendarEventView, name='event_view'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/edit/', event_views.editEventView, name='edit_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/delete/', event_views.deleteEventView, name='delete_event'),
	path('event/approve/<int:pk>/<slug:slug>/', event_views.approve_event, name='approve_event'),
	path('event/reject/<int:pk>/<slug:slug>/', event_views.reject_event, name='reject_event'),
	path('event/approval-sent/<int:pk>/<slug:slug>/', event_views.event_approval_sent, name='event_approval_sent'),
	path('event/approve-change/<int:original_pk>/<slug:original_slug>/<int:changed_pk>/<slug:changed_slug>/', event_views.approve_event_change, name='approve_event_change'),
	path('event/reject-change/<int:original_pk>/<slug:original_slug>/<int:changed_pk>/<slug:changed_slug>/', event_views.reject_event_change, name='reject_event_change'),
	path('event/deletion-request-sent/<int:pk>/<slug:slug>/', event_views.event_deletion_request_sent, name='event_deletion_request_sent'),
	path('event/approve-delete/<int:pk>/<slug:slug>/<int:deleting_user_pk>/', event_views.approve_event_delete, name='approve_event_delete'),
	path('event/reject-delete/<int:pk>/<slug:slug>/<int:deleting_user_pk>/', event_views.reject_event_delete, name='reject_event_delete'),
]

#Calendar Views
urlpatterns += [
	path('calendar/new/', event_calendar_views.newCalendarView, name='new_calendar'),
	path('calendar/<slug:slug>/', event_calendar_views.calendarView, name='calendar_view'),
	path('calendar/<slug:slug>/edit/', event_calendar_views.editCalendarView, name='edit_calendar'),
	path('calendar/<slug:slug>/delete/', event_calendar_views.deleteCalendarView, name='delete_calendar'),
]

#Location Views
urlpatterns += [
	path('location/<slug:slug>/', location_views.locationView, name='location_view'),
]

#Account Views
urlpatterns += [
	path('accounts/signup/', account_views.signup, name='signup'),
	path('accounts/<str:username>/view/', account_views.member_view, name='member_view'),
	path('accounts/account-activation-sent/', account_views.account_activation_sent, name='account_activation_sent'),
	path('accounts/activate/<str:uidb64>/<str:token>/', account_views.activate, name='activate'),
	path('accounts/<str:username>/edit/', account_views.edit_member_info, name='edit_member_info'),
	path('accounts/account-email-change-sent/', account_views.account_email_change_sent, name='account_email_change_sent'),
]