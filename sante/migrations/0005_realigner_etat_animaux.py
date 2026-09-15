from django.db import migrations


def realigner(apps, schema_editor):
    from sante.sync import realigner_animaux_depuis_suivis_ouverts
    realigner_animaux_depuis_suivis_ouverts()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('sante', '0004_suivisante_date_fin'),
    ]

    operations = [
        migrations.RunPython(realigner, noop),
    ]
