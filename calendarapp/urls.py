from django.urls import path
from . import views

urlpatterns = [
	path('', views.calendarHomeView, name='home'),
	path('event/new', views.newEventView, name='new_event'),
	path('month/<int:year>/<int:month>/', views.calendarMonthView, name='month'),
]