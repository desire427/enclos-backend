import re
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.utils import timezone


DATE_PATTERN = r'(?P<date>\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})'
TIME_PATTERN = r'(?P<hour>(?:[01]?\d|2[0-3]))(?:(?::|h)(?P<minute>[0-5]\d)?|\s*heures?)'
TIME_WITH_MARKER = re.compile(rf'(?:à|a|vers)\s*{TIME_PATTERN}', re.IGNORECASE)
DATE_TIME = re.compile(rf'{DATE_PATTERN}\s*(?:à|a|vers)\s*{TIME_PATTERN}', re.IGNORECASE)
MEDICATION_TIME = re.compile(r'\(?\s*(?P<hour>(?:[01]?\d|2[0-3]))\s*(?::|h)\s*(?P<minute>[0-5]\d)?\s*\)?', re.IGNORECASE)
RECURRING_DOSE = re.compile(r'\b(?:matin|soir|midi|nuit|chaque jour|tous les jours|quotidiennement|par jour)\b', re.IGNORECASE)
DAILY = re.compile(r'\b(?:tous les jours|chaque jour|quotidiennement)\b', re.IGNORECASE)
DURATION = re.compile(r'\bpendant\s+(\d+)\s+jours?\b', re.IGNORECASE)
END_DATE = re.compile(rf"\bjusqu['’]?au\s+{DATE_PATTERN}", re.IGNORECASE)


def _parse_date(value):
    if '-' in value:
        return date.fromisoformat(value)
    day, month, year = map(int, value.split('/'))
    return date(year, month, day)


def _parse_time(match):
    return time(int(match.group('hour')), int(match.group('minute') or 0))


def _aware_datetime(day, hour):
    return timezone.make_aware(datetime.combine(day, hour), timezone.get_current_timezone())


def parse_medication_schedules(medicaments, instructions='', prescription_date=None, now=None):
    now = now or timezone.localtime()
    start_date = prescription_date or now.date()
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    parsed = []
    seen = set()

    for source in (medicaments or '', instructions or ''):
        for line in re.split(r'[\r\n;]+', source):
            line = line.strip()
            matches = list(MEDICATION_TIME.finditer(line))
            if not line or not matches or not RECURRING_DOSE.search(line):
                continue

            medication_prefix = line[:matches[0].start()].strip(' \t,-')
            if ':' in medication_prefix:
                medication = medication_prefix.split(':', 1)[0].strip()
            else:
                medication = re.sub(
                    r'\s+\d+(?:[.,]\d+)?\s*(?:matin|soir|midi|nuit)$',
                    '', medication_prefix, flags=re.IGNORECASE,
                ).strip()
            if not medication:
                continue
            times = []
            for match in matches:
                dose_time = time(int(match.group('hour')), int(match.group('minute') or 0))
                if dose_time not in times:
                    times.append(dose_time)
            key = (medication.casefold(), tuple(times))
            if key in seen:
                continue
            seen.add(key)

            treatment = {
                'medicament': medication[:300],
                'posologie': line,
                'rappels': [],
            }
            for dose_time in times:
                due = _aware_datetime(start_date, dose_time)
                if due <= now:
                    due += timedelta(days=(now.date() - start_date).days + 1)
                treatment['rappels'].append({
                    'instruction': line,
                    'date_prochaine_prise': due,
                    'intervalle_minutes': 1440,
                    'date_fin': None,
                })
            parsed.append(treatment)

    return parsed


def parse_instructions(instructions, now=None):
    now = now or timezone.localtime()
    reminders = []

    for line in (instructions or '').splitlines():
        daily = DAILY.search(line)
        duration = DURATION.search(line)
        end_match = END_DATE.search(line)
        bounded = duration or end_match

        if daily and bounded:
            end_date_span = end_match.span('date') if end_match else None
            date_match = next(
                (match for match in re.finditer(DATE_PATTERN, line) if match.span('date') != end_date_span),
                None,
            )
            start_date = _parse_date(date_match.group('date')) if date_match else now.date()
            if duration:
                days = int(duration.group(1))
                if not 1 <= days <= 365:
                    continue
                end_date = start_date + timedelta(days=days - 1)
            else:
                end_date = _parse_date(end_match.group('date'))
            if end_date < start_date:
                continue

            for match in TIME_WITH_MARKER.finditer(line):
                due = _aware_datetime(start_date, _parse_time(match))
                if not date_match and due <= now:
                    due += timedelta(days=1)
                if due <= now or due.date() > end_date:
                    continue
                reminders.append({
                    'instruction': line.strip(),
                    'date_prochaine_prise': due,
                    'intervalle_minutes': 1440,
                    'date_fin': _aware_datetime(end_date, time.max),
                })
            continue

        for match in DATE_TIME.finditer(line):
            due = _aware_datetime(_parse_date(match.group('date')), _parse_time(match))
            if due > now:
                reminders.append({
                    'instruction': line.strip(),
                    'date_prochaine_prise': due,
                    'intervalle_minutes': None,
                    'date_fin': None,
                })

    return reminders


def process_due_reminders(now=None):
    from alertes.models import Alerte
    from sante.models import RappelOrdonnance

    now = now or timezone.now()
    reminder_ids = RappelOrdonnance.objects.filter(
        actif=True,
        date_prochaine_prise__lte=now,
        ordonnance__animal__presence='present',
    ).values_list('id', flat=True)
    created = 0

    for reminder_id in reminder_ids:
        with transaction.atomic():
            reminder = RappelOrdonnance.objects.select_for_update().select_related(
                'ordonnance__animal', 'ordonnance__ferme',
            ).get(pk=reminder_id)
            if not reminder.actif or reminder.date_prochaine_prise > now:
                continue
            if reminder.date_fin and now > reminder.date_fin:
                reminder.actif = False
                reminder.save(update_fields=['actif'])
                continue
            if reminder.dernier_rappel and now < reminder.dernier_rappel + timedelta(minutes=5):
                continue

            animal = reminder.ordonnance.animal
            animal_label = animal.nom or animal.numero_identification
            Alerte.objects.create(
                ferme=reminder.ordonnance.ferme,
                animal=animal,
                rappel_ordonnance=reminder,
                type_alerte='Rappel traitement',
                message=f"Rappel vétérinaire pour {animal_label} : {reminder.instruction}",
            )
            reminder.dernier_rappel = now
            reminder.save(update_fields=['dernier_rappel'])
            created += 1

    return created


def sync_missing_reminders():
    from sante.models import Ordonnance, RappelOrdonnance, TraitementOrdonnance

    created = 0
    for ordonnance in Ordonnance.objects.prefetch_related('rappels').iterator(chunk_size=100):
        if not ordonnance.traitements.exists():
            schedules = parse_medication_schedules(
                ordonnance.medicaments, ordonnance.instructions, ordonnance.date_prescription,
            )
            for schedule in schedules:
                treatment = TraitementOrdonnance.objects.create(
                    ordonnance=ordonnance,
                    medicament=schedule['medicament'],
                    posologie=schedule['posologie'],
                )
                RappelOrdonnance.objects.bulk_create([
                    RappelOrdonnance(ordonnance=ordonnance, traitement=treatment, **reminder)
                    for reminder in schedule['rappels']
                ])
                created += len(schedule['rappels'])
        if not ordonnance.rappels.exists():
            schedules = parse_instructions(ordonnance.instructions)
        else:
            schedules = []
        if schedules:
            RappelOrdonnance.objects.bulk_create([
                RappelOrdonnance(ordonnance=ordonnance, **schedule)
                for schedule in schedules
            ])
            created += len(schedules)
    return created