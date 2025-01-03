# Generated by Django 4.2.17 on 2024-12-31 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Hotel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city_id', models.IntegerField()),
                ('hotel_id', models.BigIntegerField()),
                ('hotel_name', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('hotel_img', models.CharField(max_length=255)),
                ('rating', models.FloatField()),
                ('room_type', models.CharField(max_length=255)),
                ('location', models.TextField()),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'hotels',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PropertyRatingReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('property_id', models.IntegerField()),
                ('rating', models.FloatField()),
                ('review', models.TextField()),
            ],
            options={
                'db_table': 'property_rating_review',
            },
        ),
        migrations.CreateModel(
            name='PropertySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('property_id', models.IntegerField()),
                ('summary', models.TextField()),
            ],
            options={
                'db_table': 'property_summary',
            },
        ),
    ]
