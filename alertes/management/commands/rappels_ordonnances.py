import time

from django.core.management.base import BaseCommand

from sante.reminders import process_due_reminders, sync_missing_reminders


class Command(BaseCommand):
    help = 'Diffuse les rappels d’ordonnance échus et les répète toutes les cinq minutes.'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=30)
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, **options):
        interval = max(5, options['interval'])
        sync_missing_reminders()
        while True:
            created = process_due_reminders()
            if created:
                self.stdout.write(f'{created} rappel(s) envoyé(s).')
            if options['once']:
                return
            time.sleep(interval)