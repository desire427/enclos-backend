from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ia_prediction', '0006_prediagnostic_conversation'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediagnostic',
            name='observations_visuelles',
            field=models.TextField(blank=True),
        ),
    ]
