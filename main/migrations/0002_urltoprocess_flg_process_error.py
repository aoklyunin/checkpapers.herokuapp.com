# Generated by Django 3.2.dev20200624102636 on 2020-07-05 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='urltoprocess',
            name='flg_process_error',
            field=models.BooleanField(default=False),
        ),
    ]