from django.urls import path
from . import calendar_views
from . import event_views
from . import event_calendar_views
from . import account_views
from . import location_views

#Calendar views
urlpatterns = [
	path('', calendar_views.home, name='home'),
	path('month/<int:year>/<int:month>/', calendar_views.month, name='month'),
	path('week/<int:year>/<int:month>/<int:first_day_of_week>/', calendar_views.week, name='week'),
	path('day/<int:year>/<int:month>/<int:day>/', calendar_views.day, name='day'),
	path('ajax_show_hide_calendars/', calendar_views.ajax_show_hide_calendars, name='ajax_show_hide_calendars'),
]

#Event Views
urlpatterns += [
	path('event/new/', event_views.new_event, name='new_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/', event_views.event_view, name='event_view'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/edit/', event_views.edit_event, name='edit_event'),
	path('event/<int:year>/<int:month>/<int:day>/<int:pk>/<slug:slug>/delete/', event_views.delete_event, name='delete_event'),
	path('event/approve/<int:pk>/<slug:slug>/', event_views.approve_event, name='approve_event'),
	path('event/reject/<int:pk>/<slug:slug>/', event_views.reject_event, name='reject_event'),
	path('event/approval-sent/<int:pk>/<slug:slug>/', event_views.event_approval_sent, name='event_approval_sent'),
	path('event/approve-change/<int:original_pk>/<slug:original_slug>/<int:changed_pk>/<slug:changed_slug>/', event_views.approve_event_change, name='approve_event_change'),
	path('event/reject-change/<int:original_pk>/<slug:original_slug>/<int:changed_pk>/<slug:changed_slug>/', event_views.reject_event_change, name='reject_event_change'),
	path('event/deletion-request-sent/<int:pk>/<slug:slug>/', event_views.event_deletion_request_sent, name='event_deletion_request_sent'),
	path('event/approve-delete/<int:pk>/<slug:slug>/', event_views.approve_event_delete, name='approve_event_delete'),
	path('event/reject-delete/<int:pk>/<slug:slug>/', event_views.reject_event_delete, name='reject_event_delete'),
	path('pending-events/', event_views.pending_events, name='pending_events'),
	path('event/ajax_pending_events/', event_views.ajax_pending_events, name='ajax_pending_events'),
]

#Calendar Views
urlpatterns += [
	path('calendar/new/', event_calendar_views.new_calendar, name='new_calendar'),
	path('calendar/<slug:slug>/', event_calendar_views.calendar_view, name='calendar_view'),
	path('calendar/<slug:slug>/edit/', event_calendar_views.edit_calendar, name='edit_calendar'),
	path('calendar/<slug:slug>/delete/', event_calendar_views.delete_calendar, name='delete_calendar'),
	path('calendar/approval-sent/<slug:slug>/', event_calendar_views.calendar_approval_sent, name='calendar_approval_sent'),
	path('calendar/approve-calendar/<slug:slug>/', event_calendar_views.approve_calendar, name='approve_calendar'),
	path('calendar/reject-calendar/<slug:slug>/', event_calendar_views.reject_calendar, name='reject_calendar'),
	path('pending-calendars/', event_calendar_views.pending_calendars, name='pending_calendars'),
]

#Location Views
urlpatterns += [
	path('location/new/', location_views.new_location, name='new_location'),
	path('location/<slug:slug>/', location_views.location_view, name='location_view'),
	path('location/<slug:slug>/edit/', location_views.edit_location, name='edit_location'),
	path('location/<slug:slug>/delete/', location_views.delete_location, name='delete_location'),
	path('location/approval-sent/<slug:slug>/', location_views.location_approval_sent, name='location_approval_sent'),
	path('location/approve-location/<slug:slug>/', location_views.approve_location, name='approve_location'),
	path('location/reject-location/<slug:slug>/', location_views.reject_location, name='reject_location'),
	path('pending-locations/', location_views.pending_locations, name='pending_locations'),
]

#Account Views
urlpatterns += [
	path('accounts/signup/', account_views.signup, name='signup'),
	path('accounts/account-activation-sent/', account_views.account_activation_sent, name='account_activation_sent'),
	path('accounts/account-email-change-sent/', account_views.account_email_change_sent, name='account_email_change_sent'),
	path('accounts/<str:username>/', account_views.member_view, name='member_view'),
	path('accounts/activate/<str:uidb64>/<str:token>/', account_views.activate, name='activate'),
	path('accounts/<str:username>/edit/', account_views.edit_member_info, name='edit_member_info'),
]