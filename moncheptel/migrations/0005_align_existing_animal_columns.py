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
            if isinstance(self.field, models.UUIDField) and self.field.unique:
                field = to_state.apps.get_model(app_label, self.model_name)._meta.get_field(self.name)
                nullable_field = field.clone()
                nullable_field.null = True
                nullable_field.unique = False
                nullable_field.default = models.NOT_PROVIDED
                nullable_field.set_attributes_from_name(self.name)
                nullable_field.model = model
                schema_editor.add_field(model, nullable_field)

                quote = schema_editor.quote_name
                table_name = quote(table)
                column = quote(column_name)
                primary_key = quote(model._meta.pk.column)
                with schema_editor.connection.cursor() as cursor:
                    cursor.execute(f'SELECT {primary_key} FROM {table_name}')
                    updates = [
                        (uuid.uuid4(), row[0])
                        for row in cursor.fetchall()
                    ]
                    cursor.executemany(
                        f'UPDATE {table_name} SET {column} = %s WHERE {primary_key} = %s',
                        updates,
                    )
                schema_editor.alter_field(model, nullable_field, field)
                return
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
