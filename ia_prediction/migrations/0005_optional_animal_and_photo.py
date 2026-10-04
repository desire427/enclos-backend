from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ia_prediction', '0004_pre_diagnostic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prediagnostic',
            name='animal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pre_diagnostics', to='moncheptel.animal'),
        ),
        migrations.AlterField(
            model_name='prediagnostic',
            name='photo',
            field=models.ImageField(blank=True, upload_to='pre_diagnostics/'),
        ),
    ]