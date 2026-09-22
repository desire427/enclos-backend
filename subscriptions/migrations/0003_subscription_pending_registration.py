from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_subscription_moyen_paiement_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='subscriptions', to='auth.user', verbose_name='Utilisateur'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='inscription_en_attente',
            field=models.JSONField(blank=True, default=dict, verbose_name='Inscription en attente'),
        ),
    ]