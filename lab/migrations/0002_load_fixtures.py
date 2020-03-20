from django.core.management import call_command
from django.db import migrations


def forwards_func(apps, schema_editor):
    print('Aplicando carga inicial')
    call_command('loaddata','carga_inicial.json',verbosity=2)
    print('Carga inicial aplicada')


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    initial = False
    dependencies = [('lab', '0001_initial'), ]
    operations = [migrations.RunPython(
        forwards_func, reverse_func, elidable=False)]
