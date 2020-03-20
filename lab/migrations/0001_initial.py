# Generated by Django 3.0.4 on 2020-03-18 22:29

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(db_index=True, error_messages={'unique': 'A user with that username already exists.'}, help_text='Número SIAPE no caso de servidores ou matrícula no caso de docentes ou terceirizados', max_length=15, unique=True, verbose_name='matrícula')),
                ('is_professor', models.BooleanField(default=True, help_text='Indica se o usuário é um professor ou não?', verbose_name='É professor?')),
            ],
            options={
                'verbose_name': 'usuário',
                'verbose_name_plural': 'usuários',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='ConfigLab',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('configuracao', models.IntegerField(choices=[(1, 'Tamanho máximo permitido para o envio do roteiro em MB.'), (2, '#Permitir estourar o estoque.'), (3, '#Permitir sobreposição de requisições (mesma data/hora e local)'), (4, '#Permitir requisições aos domingos'), (5, '#Permitir requisições aos sábados'), (6, '#Permitir requisições em feriados'), (7, '#Horário mínimo para requisião(HHMM)'), (8, '#Horário máximo para requisião(HHMM)'), (9, '#Enviar e-mail aos professores'), (10, '#Enviar e-mail aos requisitantes'), (11, '#Enviar e-mail aos técnicos'), (12, '#Antecedência mínima da requisição (Em horas)')], unique=True, verbose_name='configuração')),
                ('valor', models.IntegerField(verbose_name='valor')),
            ],
            options={
                'verbose_name': 'Configuração',
                'verbose_name_plural': 'Configurações',
                'ordering': ('configuracao',),
            },
        ),
        migrations.CreateModel(
            name='Escopo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='nome')),
                ('status', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Ativo'), (2, 'Inativo')], default=1, verbose_name='status')),
                ('tecnicos', models.ManyToManyField(limit_choices_to={'is_active': True, 'is_staff': True}, to=settings.AUTH_USER_MODEL, verbose_name='técnicos')),
            ],
            options={
                'verbose_name': 'Escopo',
                'verbose_name_plural': 'Escopos',
                'ordering': ('nome',),
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(help_text='Nome do Item', max_length=60, verbose_name='Nome')),
                ('descricao', models.TextField(help_text='Descrição Detalhada do Item', max_length=400, verbose_name='Descrição')),
                ('tipo', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Bem Permanente'), (2, 'Material de Consumo')], db_index=True, default=1, help_text='Tipo Item', verbose_name='Tipo')),
                ('status', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Ativo'), (2, 'Inativo')], db_index=True, default=1, help_text='Situação do Item', verbose_name='Status')),
                ('escopo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='lab.Escopo', verbose_name='escopo')),
            ],
            options={
                'verbose_name': 'item',
                'verbose_name_plural': 'itens',
                'ordering': ('nome',),
            },
        ),
        migrations.CreateModel(
            name='ItemRequisitado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_qt_solicitado', models.PositiveSmallIntegerField(default=0, help_text='Quantidade solicitada', verbose_name='Quantidade solicitada')),
                ('_qt_estoque', models.PositiveSmallIntegerField(default=0, help_text='Quantidade em estoque quanto solicitado', verbose_name='Estoque no requisicão')),
                ('_qt_aprovado', models.PositiveSmallIntegerField(default=0, help_text='Quantidade aprovada', verbose_name='Quantidade aprovada')),
                ('_qt_devolvido', models.PositiveSmallIntegerField(default=0, verbose_name='Quantidade devolvida')),
                ('c_aprovado', models.TextField(default='', verbose_name='Comentário deixado na aprovação')),
                ('c_devolvido', models.TextField(default='', verbose_name='Comentário deixado na devolução')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ItensRequisitados', to='lab.Item', verbose_name='Item Requisitado')),
            ],
        ),
        migrations.CreateModel(
            name='Laboratorio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(db_index=True, help_text='Código do Laboratório', max_length=20, unique=True, verbose_name='Código')),
                ('descricao', models.CharField(help_text='Descrição do Laboratório', max_length=60, verbose_name='Descrição')),
                ('sala', models.CharField(db_index=True, help_text='Sala onde está localizado o Laboratório', max_length=20, unique=True, verbose_name='Sala')),
                ('capacidade_maxima', models.PositiveSmallIntegerField(default=100, help_text='Capacidade máxima de alunos', verbose_name='Máximo de alunos')),
                ('status', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Ativo'), (2, 'Inativo')], db_index=True, default=1, help_text='Situação do Laboratório', verbose_name='Status')),
                ('escopo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='lab.Escopo', verbose_name='escopo')),
            ],
            options={
                'verbose_name': 'laboratório',
                'verbose_name_plural': 'laboratórios',
            },
        ),
        migrations.CreateModel(
            name='Unidade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(db_index=True, help_text='Código da unidade de medida', max_length=20, unique=True, verbose_name='Código')),
                ('descricao', models.CharField(help_text='Descrição da unidade de medida', max_length=60, verbose_name='Descrição')),
                ('status', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Ativo'), (2, 'Inativo')], db_index=True, default=1, help_text='Situação da unidade', verbose_name='Status')),
            ],
            options={
                'verbose_name': 'unidade de medida',
                'verbose_name_plural': 'unidades de medida',
            },
        ),
        migrations.CreateModel(
            name='Requisicao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disciplina', models.CharField(help_text='Disciplina', max_length=60, verbose_name='Disciplina')),
                ('tipo_atividade', models.PositiveSmallIntegerField(choices=[(1, 'Aula'), (2, 'Projeto')], default=1, help_text='Finalidade da requisição (Aula/Projeto)', verbose_name='Tipo de atividade')),
                ('pratica', models.TextField(help_text='Descrição da atividade a ser realizada', verbose_name='Prática')),
                ('qt_alunos', models.IntegerField(help_text='Quantidade de Alunos previsto', verbose_name='Quantidade de Alunos')),
                ('precisa_tecnico', models.BooleanField(default=False, help_text='Será necessário a presença do técnico durante o evento?', verbose_name='Precisa o Técnico estar presente?')),
                ('roteiro', models.FileField(blank=True, help_text='Roteiro da prática se existir', null=True, upload_to='roteiros/', verbose_name='Roteiro da prática (Se existir)')),
                ('data', models.DateField(help_text='Data do evento')),
                ('hora_inicio', models.TimeField(help_text='Horário de inicio do evento', verbose_name='Horário de Início')),
                ('hora_fim', models.TimeField(help_text='Horário de encerramento do evento', verbose_name='Encerramento')),
                ('observacoes', models.TextField(blank=True, help_text='Observações sobre o evento', null=True, verbose_name='Observações')),
                ('itens_json', models.TextField(blank=True, help_text='Itens solicitados', null=True, verbose_name='Itens solicitados')),
                ('ocorrencias', models.TextField(blank=True, default='', help_text='Ocorrências durando o uso do laboratório', verbose_name='Ocorrências')),
                ('status', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Requerido'), (2, 'Aprovado'), (3, 'Aprovado*'), (4, 'Atendido'), (5, 'Rejeitado'), (6, 'Finalizado'), (7, 'Cancelado')], db_index=True, default=1, help_text='Status da requisição', verbose_name='Status')),
                ('escopo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='lab.Escopo', verbose_name='escopo')),
                ('itens', models.ManyToManyField(related_name='requisicoes', through='lab.ItemRequisitado', to='lab.Item', verbose_name='Item na requisição')),
                ('laboratorio', models.ForeignKey(limit_choices_to={'status': 1}, on_delete=django.db.models.deletion.PROTECT, to='lab.Laboratorio', verbose_name='Laboratório')),
                ('professor', models.ForeignKey(limit_choices_to={'is_active': True, 'is_professor': True}, on_delete=django.db.models.deletion.PROTECT, related_name='requisicoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'requisição',
                'verbose_name_plural': 'requisições',
                'ordering': ('-data', '-hora_inicio'),
            },
        ),
        migrations.AddField(
            model_name='itemrequisitado',
            name='requisicao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ItensRequisitados', to='lab.Requisicao', verbose_name='Requisicao Contido'),
        ),
        migrations.AddField(
            model_name='item',
            name='unidade',
            field=models.ForeignKey(default=1, limit_choices_to={'status': 1}, on_delete=django.db.models.deletion.PROTECT, to='lab.Unidade'),
        ),
        migrations.CreateModel(
            name='HistoricoEstoque',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')),
                ('movimentacao', models.IntegerField(verbose_name='quantidade')),
                ('estoque_anterior', models.IntegerField(default=0, verbose_name='estoque anterior')),
                ('descricao', models.TextField(verbose_name='descrição')),
                ('item', models.ForeignKey(limit_choices_to={'status': 1, 'tipo': 2}, on_delete=django.db.models.deletion.PROTECT, related_name='historicosEstoque', to='lab.Item', verbose_name='Item')),
                ('requisicao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='historicosEstoque', to='lab.Requisicao', verbose_name='requisição')),
            ],
            options={
                'verbose_name': 'Evento de Estoque',
                'verbose_name_plural': 'Histórico do Estoque de Materias',
                'ordering': ('-data_hora',),
            },
        ),
        migrations.CreateModel(
            name='Ferramenta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tombo', models.CharField(help_text='Número patrimônial da ferramenta', max_length=10, unique=True, verbose_name='Tombo')),
                ('observacao', models.TextField(blank=True, help_text='Observação relevante sobre a ferramenta', max_length=400, verbose_name='Observações')),
                ('status', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Ativo'), (2, 'Inativo')], db_index=True, default=1, help_text='Situação do ferramenta', verbose_name='Status')),
                ('item', models.ForeignKey(limit_choices_to={'tipo': 1}, on_delete=django.db.models.deletion.PROTECT, related_name='ferramentas', to='lab.Item')),
            ],
            options={
                'verbose_name': 'ferramenta',
                'verbose_name_plural': 'ferramentas',
            },
        ),
        migrations.CreateModel(
            name='EstoqueMaterial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.IntegerField(default=0, help_text='Quantidade em estoque do Material', verbose_name='Quantidade em Estoque')),
                ('item', models.ForeignKey(limit_choices_to={'tipo': 2}, on_delete=django.db.models.deletion.PROTECT, related_name='estoqueMateriais', to='lab.Item')),
            ],
            options={
                'verbose_name': 'estoque de material',
                'verbose_name_plural': 'estoque de materiais',
            },
        ),
        migrations.CreateModel(
            name='Cesta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50)),
                ('itens', models.TextField()),
                ('escopo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lab.Escopo', verbose_name='escopo')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cestas', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
        ),
        migrations.CreateModel(
            name='Aviso',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=50, verbose_name='título')),
                ('mensagem', models.TextField(verbose_name='menssagem')),
                ('inicio', models.DateTimeField(verbose_name='início de vigência')),
                ('fim', models.DateTimeField(verbose_name='fim de vigência')),
                ('importante', models.BooleanField(verbose_name='em destaque')),
                ('status', models.PositiveSmallIntegerField(choices=[(None, 'Indefinido'), (1, 'Ativo'), (2, 'Inativo')], default=1, verbose_name='status')),
                ('escopo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='lab.Escopo', verbose_name='escopo')),
            ],
            options={
                'verbose_name': 'Aviso',
                'verbose_name_plural': 'Avisos',
                'ordering': ('-importante', 'inicio', 'fim'),
            },
        ),
        migrations.CreateModel(
            name='Auditoria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('noque', models.IntegerField(choices=[(1, 'Usuario'), (2, 'Laboratorio'), (3, 'Unidade'), (4, 'Item'), (5, 'Ferramenta'), (6, 'Estoquematerial'), (7, 'Requisicao'), (8, 'Itemrequisitado')], verbose_name='Modelo Envolvido')),
                ('noqual', models.IntegerField(choices=[(1, 'Usuario'), (2, 'Laboratorio'), (3, 'Unidade'), (4, 'Item'), (5, 'Ferramenta'), (6, 'Estoquematerial'), (7, 'Requisicao'), (8, 'Itemrequisitado')], verbose_name='Id do Modelo envolvido')),
                ('quando', models.DateTimeField(auto_now_add=True, verbose_name='quando o evento ocorreu')),
                ('oque', models.IntegerField(choices=[(1, 'Criar Requisicao'), (2, 'Add Comentario'), (3, 'Cancelar Requisicao'), (4, 'Finalizar Requisicao'), (5, 'Rejeitar Requisicao'), (6, 'Aprovar Requisicao'), (7, 'Aprovar Parcialmente Requisicao'), (8, 'Atender Requisicao'), (9, 'Modificar Dados Pessoais')], verbose_name='Ação Realizada')),
                ('quem', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Quem realizou a acão')),
            ],
        ),
        migrations.AddField(
            model_name='usuario',
            name='escopo_default',
            field=models.ForeignKey(blank=True, limit_choices_to={'status': 1}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios', to='lab.Escopo', verbose_name='escopo padrão'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='itemrequisitado',
            unique_together={('item', 'requisicao')},
        ),
    ]
