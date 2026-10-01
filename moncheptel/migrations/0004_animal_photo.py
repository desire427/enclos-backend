from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('moncheptel', '0003_remove_animal_statut_animal_etat_sante_and_more')]
    operations = [
        migrations.AddField(
            model_name='animal',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='animaux/', verbose_name='Photo'),
        ),
    ]
