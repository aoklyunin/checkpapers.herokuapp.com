# Generated by Django 3.2.dev20200624102636 on 2020-07-02 14:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_auto_20200702_1700'),
    ]

    operations = [
        migrations.RenameField(
            model_name='paper',
            old_name='thruth',
            new_name='truth',
        ),
    ]