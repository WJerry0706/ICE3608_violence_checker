# Generated by Django 4.2.5 on 2024-12-16 14:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('UserAuth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Resume',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, verbose_name='简历名称')),
                ('file_path', models.CharField(max_length=200, verbose_name='简历路径')),
                ('belong_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='UserAuth.user', verbose_name='所属用户')),
            ],
        ),
    ]