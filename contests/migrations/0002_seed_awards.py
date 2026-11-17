from django.db import migrations

INITIAL_AWARDS = [("優勝", 1), ("準優勝", 2), ("審査員特別賞", 3)]


def seed(apps, schema_editor):
    Award = apps.get_model("contests", "Award")
    for name, order in INITIAL_AWARDS:
        Award.objects.get_or_create(name=name, defaults={"order": order})


def unseed(apps, schema_editor):
    Award = apps.get_model("contests", "Award")
    Award.objects.filter(name__in=[n for n, _ in INITIAL_AWARDS], entries__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("contests", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
