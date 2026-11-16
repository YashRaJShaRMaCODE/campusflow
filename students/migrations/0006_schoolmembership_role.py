from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("students", "0005_studentexportrequest")]

    operations = [
        migrations.AddField(
            model_name="schoolmembership",
            name="role",
            field=models.CharField(
                choices=[("manager", "Manager"), ("viewer", "Viewer")],
                default="manager",
                max_length=10,
            ),
        ),
    ]
