"""Record dataset restoration in the append-only audit event type choices."""
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("annotations", "0002_auditevent")]
    operations = [
        migrations.AlterField(
            model_name="auditevent",
            name="event_type",
            field=models.CharField(choices=[
                ("task.claimed", "Task claimed"), ("task.submitted", "Task submitted"),
                ("task.reviewed", "Task reviewed"), ("annotation.created", "Annotation created"),
                ("annotation.updated", "Annotation updated"), ("dataset.tasks_imported", "Tasks imported"),
                ("dataset.version_created", "Dataset version created"),
                ("dataset.version_restored", "Dataset version restored"),
            ], max_length=64),
        ),
    ]
