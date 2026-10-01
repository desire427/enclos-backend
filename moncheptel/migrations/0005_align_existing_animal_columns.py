import uuid
from django.db import migrations, models


class AddFieldIfColumnMissing(migrations.AddField):
    """Adopt fields already created by the legacy QR migrations in some databases."""
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        table = model._meta.db_table
        with schema_editor.connection.cursor() as cursor:
            columns = {column.name for column in schema_editor.connection.introspection.get_table_description(cursor, table)}
        column_name = self.field.db_column or self.name
        if column_name not in columns:
            super().database_forwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):
    dependencies = [('moncheptel', '0004_animal_photo')]
    operations = [
        AddFieldIfColumnMissing(
            model_name='animal', name='poids_actuel',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='Poids actuel (kg)'),
        ),
        AddFieldIfColumnMissing(
            model_name='animal', name='qr_code',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Code QR'),
        ),
        AddFieldIfColumnMissing(
            model_name='animal', name='qr_uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Identifiant QR'),
        ),
        AddFieldIfColumnMissing(
            model_name='animal', name='qr_tracking_code',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Code de suivi QR'),
        ),
        AddFieldIfColumnMissing(
            model_name='animal', name='qr_tracking_uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Identifiant de suivi QR'),
        ),
    ]
