# Generated by Django 3.0.6 on 2020-06-05 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20200604_1632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimiento',
            name='concepto',
            field=models.CharField(blank=True, choices=[('C1', 'COMISION GENERACION 1'), ('C2', 'COMISION GENERACION 2'), ('C3', 'COMISION GENERACION 3'), ('CI', 'CICLAJE'), ('PN', 'PAGO POR NIVEL'), ('CS', 'CARGA DE SALDO'), ('RS', 'RETIRO DE SALDO')], default='', max_length=2, null=True),
        ),
    ]