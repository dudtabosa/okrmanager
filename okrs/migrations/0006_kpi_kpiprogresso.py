# Generated by Django 4.2.7 on 2025-04-13 19:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('okrs', '0005_keyresultprogresso_data_progresso'),
    ]

    operations = [
        migrations.CreateModel(
            name='KPI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200)),
                ('descricao', models.TextField()),
                ('tipo_valor', models.CharField(choices=[('NUMERO', 'Número'), ('PORCENTAGEM', 'Porcentagem'), ('MOEDA', 'Moeda')], default='NUMERO', max_length=20)),
                ('valor_target', models.DecimalField(decimal_places=2, max_digits=10)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('ativo', models.BooleanField(default=True)),
                ('diretoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='okrs.diretoria')),
                ('time', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='okrs.time')),
            ],
            options={
                'verbose_name': 'KPI',
                'verbose_name_plural': 'KPIs',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='KPIProgresso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_atual', models.DecimalField(decimal_places=2, max_digits=10)),
                ('data_medicao', models.DateField()),
                ('observacoes', models.TextField(blank=True, null=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('atualizado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('kpi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progressos', to='okrs.kpi')),
            ],
            options={
                'verbose_name': 'Progresso do KPI',
                'verbose_name_plural': 'Progressos dos KPIs',
                'ordering': ['-data_medicao'],
            },
        ),
    ]
