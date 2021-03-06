# Generated by Django 3.0.4 on 2020-03-23 21:42

from django.db import migrations, models
import ulid.api


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UploadFile',
            fields=[
                ('id', models.CharField(default=ulid.api.new, editable=False, max_length=26, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('file', models.FileField(upload_to='', verbose_name='CSVファイル')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
