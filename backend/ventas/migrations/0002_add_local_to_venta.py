from django.db import migrations, models

def set_default_local(apps, schema_editor):
    Local = apps.get_model("core_app", "Local")
    Venta = apps.get_model("ventas", "Venta")
    default_local, _ = Local.objects.get_or_create(
        nombre="Default",
        defaults={"activo": True},
    )
    Venta.objects.filter(local__isnull=True).update(local_id=default_local.id)

class Migration(migrations.Migration):

    dependencies = [
        ("core_app", "0001_initial"),   # ajustá si tu número difiere
        ("ventas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="venta",
            name="local",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="ventas",
                to="core_app.local",
            ),
        ),
        migrations.RunPython(set_default_local, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="venta",
            name="local",
            field=models.ForeignKey(
                null=False,
                on_delete=models.deletion.CASCADE,
                related_name="ventas",
                to="core_app.local",
            ),
        ),
    ]
