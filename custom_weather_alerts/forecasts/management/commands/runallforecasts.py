import datetime

from django.core.management.base import BaseCommand

from forecasts.models import ForecastProfile



class Command(BaseCommand):
    help = "runs all forecasts"

    def handle(self, *args, **options):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        running = True
        while running:
            p = ForecastProfile.objects.filter(last_updated__lt=today).first()
            if p is None:
                self.stdout.write("No more forecasts to run")
                running = False
                break
            else:
                self.stdout.write("Checking forecast for someone...")
                p.CheckForecast()
