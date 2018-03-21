from django.core.management.base import BaseCommand
from calendarapp.models import Event
from django.utils import timezone
import datetime

class Command(BaseCommand):

    help = 'Deletes unapproved events after 4 days'

    def handle(self, *args, **options):
        for event in Event.objects.filter(approved=False):
        	if event.date_created + datetime.timedelta(days=4) < timezone.now():
        		event.delete()

        self.stdout.write(self.style.SUCCESS('Successfully purged unapproved events that were created four days ago!'))