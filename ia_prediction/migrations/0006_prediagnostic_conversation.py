from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('historique', '0002_initial'),
        ('ia_prediction', '0005_optional_animal_and_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediagnostic',
            name='conversation',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='prediagnostic',
            name='espece_image',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='prediagnostic',
            name='historique_evenement',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pre_diagnostics', to='historique.historiqueevenement'),
        ),
        migrations.AddField(
            model_name='prediagnostic',
            name='utilisateur',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pre_diagnostics', to=settings.AUTH_USER_MODEL),
        ),
    ]