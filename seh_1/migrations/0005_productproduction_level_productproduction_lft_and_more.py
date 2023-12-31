# Generated by Django 4.2.5 on 2023-11-16 06:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0004_alter_productproduction_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productproduction',
            name='level',
            field=models.PositiveIntegerField(default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productproduction',
            name='lft',
            field=models.PositiveIntegerField(default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productproduction',
            name='parent',
            field=models.ForeignKey(blank=True, limit_choices_to={'parent__isnull': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='seh_1.productproduction', verbose_name="Bo'limlar"),
        ),
        migrations.AddField(
            model_name='productproduction',
            name='rght',
            field=models.PositiveIntegerField(default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productproduction',
            name='tree_id',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
            preserve_default=False,
        ),
    ]
