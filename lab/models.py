import json

#from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _


class STATUS_BASICO(models.IntegerChoices):
    ATIVO = 1, _('Ativo')
    INATIVO = 2, _('Inativo')

    __empty__ = _('Indefinido')


class SR(models.IntegerChoices):
    REQUERIDO = 1, _('Requerido')
    APROVADO = 2, _('Aprovado')
    APROVADO_PARCIAL = 3, _('Aprovado*')
    ATENDIDO = 4, _('Atendido')
    REJEITADO = 5, _('Rejeitado')
    FINALIZADO = 6, _('Finalizado')
    CANCELADO = 7, _('Cancelado')
    __empty__ = _('Indefinido')


class Usuario(AbstractUser):
    username = models.CharField(
        _('matrícula'),
        max_length=15,
        unique=True,
        db_index=True,
        help_text=_(
            'Número SIAPE no caso de servidores ou matrícula no caso de docentes ou terceirizados'),
        error_messages={
            'unique': _("A user with that username already exists."),
        }
    )

    is_professor = models.BooleanField(
        help_text='Indica se o usuário é um professor ou não?',
        verbose_name='É professor?',
        default=True
    )

    _escopo = None

    escopo_default = models.ForeignKey("Escopo",
                                       verbose_name=_("escopo padrão"),
                                       on_delete=models.SET_NULL,
                                       related_name='usuarios',
                                       limit_choices_to={
                                           'status': STATUS_BASICO.ATIVO},
                                       null=True,
                                       blank=True
                                       )

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return str(self.get_full_name()) + ' (' + str(self.username) + ')'

    def save(self, *args, **kwargs):
        super(Usuario, self).save(*args, **kwargs)
        grupo = Group.objects.get(name='users_default')
        if self.is_staff and self.is_active:
            grupo.user_set.add(self)
        else:
            grupo.user_set.remove(self)

    @property
    def requisicoes_realizadas(self, status=0):
        if status > 0:
            return list(Requisicao.objects.filter(professor=self, status=status))
        else:
            return list(Requisicao.objects.filter(professor=self))

    def get_escopos(self):
        return Escopo.objects.filter(status=STATUS_BASICO.ATIVO)

    @property
    def escopo_selecionado(self):
        if self._escopo:
            return self._escopo
        return self.escopo_default

    @escopo_selecionado.setter
    def escopo_selecionado(self, value):
        self._escopo = value


class Laboratorio(models.Model):

    escopo = models.ForeignKey("Escopo", verbose_name=_(
        "escopo"), on_delete=models.PROTECT)

    codigo = models.CharField(
        unique=True,
        db_index=True,
        max_length=20,
        help_text='Código do Laboratório',
        verbose_name='Código',
    )

    descricao = models.CharField(
        max_length=60,
        help_text='Descrição do Laboratório',
        verbose_name='Descrição',
    )

    sala = models.CharField(
        unique=True,
        db_index=True,
        max_length=20,
        help_text='Sala onde está localizado o Laboratório',
        verbose_name='Sala',
    )

    capacidade_maxima = models.PositiveSmallIntegerField(
        help_text='Capacidade máxima de alunos',
        verbose_name='Máximo de alunos',
        default=100,
    )

    status = models.PositiveSmallIntegerField(
        db_index=True,
        choices=STATUS_BASICO.choices,
        help_text='Situação do Laboratório',
        verbose_name='Status',
        default=STATUS_BASICO.ATIVO
    )

    class Meta:
        verbose_name = 'laboratório'
        verbose_name_plural = 'laboratórios'

    def __str__(self):
        return str(self.descricao) + ' (' + str(self.codigo) + ')'


class Unidade(models.Model):
    codigo = models.CharField(
        unique=True,
        db_index=True,
        max_length=20,
        help_text='Código da unidade de medida',
        verbose_name='Código'
    )

    descricao = models.CharField(
        max_length=60,
        help_text='Descrição da unidade de medida',
        verbose_name='Descrição',
    )

    status = models.PositiveSmallIntegerField(
        db_index=True,
        choices=STATUS_BASICO.choices,
        help_text='Situação da unidade',
        verbose_name='Status',
        default=STATUS_BASICO.ATIVO,
    )

    class Meta:
        verbose_name = 'unidade de medida'
        verbose_name_plural = 'unidades de medida'

    def __str__(self):
        return str(self.descricao) + '(' + str(self.codigo) + ')'


class Item(models.Model):
    escopo = models.ForeignKey("Escopo", verbose_name=_(
        "escopo"), on_delete=models.PROTECT)

    nome = models.CharField(
        max_length=60,
        help_text='Nome do Item',
        verbose_name='Nome',
    )

    descricao = models.TextField(
        max_length=400,
        help_text='Descrição Detalhada do Item',
        verbose_name='Descrição',
    )

    class TIPOS_DE_ITENS(models.IntegerChoices):
        FERRAMENTA = 1, _('Bem Permanente')
        MATERIAL = 2, _('Material de Consumo')

        __empty__ = _('Indefinido')

    tipo = models.PositiveSmallIntegerField(
        db_index=True,
        choices=TIPOS_DE_ITENS.choices,
        help_text='Tipo Item',
        verbose_name='Tipo',
        default=TIPOS_DE_ITENS.FERRAMENTA,
    )

    unidade = models.ForeignKey(
        'Unidade',
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'status': STATUS_BASICO.ATIVO},
        default=STATUS_BASICO.ATIVO,
    )
    status = models.PositiveSmallIntegerField(
        db_index=True,
        choices=STATUS_BASICO.choices,
        help_text='Situação do Item',
        verbose_name='Status',
        default=STATUS_BASICO.ATIVO,
    )

    class Meta:
        verbose_name = 'item'
        verbose_name_plural = 'itens'
        ordering = ('nome', )

    def __str__(self):
        return str(self.nome)

    @property
    def estoque(self):
        if self.tipo == self.TIPOS_DE_ITENS.FERRAMENTA:
            try:
                return Ferramenta.objects.filter(status=STATUS_BASICO.ATIVO, item=self).count()
            except Ferramenta.DoesNotExist:
                return 0
        else:
            try:
                return EstoqueMaterial.objects.get(item=self).quantidade
            except EstoqueMaterial.DoesNotExist:
                return 0

    @estoque.setter
    def estoque(self, value):
        if self.tipo == self.TIPOS_DE_ITENS.MATERIAL:
            try:
                e = EstoqueMaterial.objects.get(item=self)
                e.quantidade = value
                e.save()
            except EstoqueMaterial.DoesNotExist:
                e = EstoqueMaterial(item=self, quantidade=value).save()

        else:  # Caso item patrimonial
            raise AssertionError(
                "Itens patrimoniais tem seu estoque definido pela soma dos itens cadastrados!")

    @property
    def get_lista_itens_ativos(self):
        return Item.objects.filter(status=STATUS_BASICO.ATIVO)

    @staticmethod
    def baixar_estoque(requisicao, desfazer=False, devolucao=False):
        fator = -1 if desfazer else 1
        for ir in requisicao.itens_requisitados:
            if ir.item.tipo == Item.TIPOS_DE_ITENS.MATERIAL:
                hist_estoque = HistoricoEstoque(
                    item=ir.item, requisicao=requisicao)
                if devolucao:
                    hist_estoque.movimentacao = fator * int(ir.devolvido)
                    hist_estoque.descricao = "Devolvido" if not desfazer else "Cancelada devolução"
                else:
                    hist_estoque.movimentacao = -fator * int(ir.aprovado)
                    hist_estoque.descricao = "Reservado/Consumido" if not desfazer else "Reserva cancelada"
                hist_estoque.save()


class Ferramenta(models.Model):
    item = models.ForeignKey(
        'Item',
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'tipo': Item.TIPOS_DE_ITENS.FERRAMENTA},
        related_name='ferramentas'
    )

    tombo = models.CharField(
        max_length=10,
        help_text='Número patrimônial da ferramenta',
        verbose_name='Tombo',
        blank=False,
        null=False,
        unique=True,
    )

    observacao = models.TextField(
        max_length=400,
        blank=True,
        help_text='Observação relevante sobre a ferramenta',
        verbose_name='Observações',
    )

    status = models.PositiveSmallIntegerField(
        db_index=True,
        choices=STATUS_BASICO.choices,
        help_text='Situação do ferramenta',
        verbose_name='Status',
        default=STATUS_BASICO.ATIVO,
    )

    class Meta:
        verbose_name = 'ferramenta'
        verbose_name_plural = 'ferramentas'

    def __str__(self):
        return '{0} - (TOMBO: {1})'.format(str(self.item), self.tombo)


class EstoqueMaterial(models.Model):
    item = models.ForeignKey(
        'Item',
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'tipo': Item.TIPOS_DE_ITENS.MATERIAL},
        related_name='estoqueMateriais'
    )
    quantidade = models.IntegerField(
        help_text='Quantidade em estoque do Material',
        verbose_name='Quantidade em Estoque',
        default=0,
    )

    class Meta:
        verbose_name = 'estoque de material'
        verbose_name_plural = 'estoque de materiais'

    def __str__(self):
        return "{0} ({1} {2})".format(self.item.nome, self.quantidade, self.item.unidade.descricao)


class Requisicao(models.Model):
    escopo = models.ForeignKey("Escopo", verbose_name=_(
        "escopo"), on_delete=models.PROTECT)

    professor = models.ForeignKey(
        'Usuario',
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'is_active': True, 'is_professor': True},
        related_name="requisicoes"
    )

    disciplina = models.CharField(
        max_length=60,
        help_text='Disciplina',
        verbose_name='Disciplina',
    )

    class TIPOS_DE_ATIVIDADE(models.IntegerChoices):
        AULA = 1, _('Aula')
        PROJETO = 2, _('Projeto')

    tipo_atividade = models.PositiveSmallIntegerField(
        choices=TIPOS_DE_ATIVIDADE.choices,
        help_text='Finalidade da requisição (Aula/Projeto)',
        verbose_name='Tipo de atividade',
        default=TIPOS_DE_ATIVIDADE.AULA,
    )

    pratica = models.TextField(
        blank=False,
        null=False,
        help_text='Descrição da atividade a ser realizada',
        verbose_name='Prática',
    )

    laboratorio = models.ForeignKey(
        'laboratorio',
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'status': STATUS_BASICO.ATIVO},
        verbose_name='Laboratório',
    )

    qt_alunos = models.IntegerField(
        null=False,
        help_text='Quantidade de Alunos previsto',
        verbose_name='Quantidade de Alunos',
    )

    precisa_tecnico = models.BooleanField(
        default=False,
        help_text='Será necessário a presença do técnico durante o evento?',
        verbose_name='Precisa o Técnico estar presente?',
    )
    roteiro = models.FileField(

        upload_to='roteiros/',
        blank=True,
        null=True,
        help_text='Roteiro da prática se existir',
        verbose_name='Roteiro da prática (Se existir)',
    )
    data = models.DateField(
        help_text='Data do evento'
    )

    hora_inicio = models.TimeField(
        help_text='Horário de inicio do evento',
        verbose_name='Horário de Início',
    )

    hora_fim = models.TimeField(
        help_text='Horário de encerramento do evento',
        verbose_name='Encerramento',
    )

    observacoes = models.TextField(
        blank=True,
        null=True,
        help_text='Observações sobre o evento',
        verbose_name='Observações',
    )

    itens_json = models.TextField(
        blank=True,
        null=True,
        help_text='Itens solicitados',
        verbose_name='Itens solicitados',
    )

    itens = models.ManyToManyField(
        'Item',
        verbose_name=_('Item na requisição'),
        through='ItemRequisitado',
        through_fields=('requisicao', 'item'),
        related_name='requisicoes',
    )

    ocorrencias = models.TextField(
        blank=True,
        help_text='Ocorrências durando o uso do laboratório',
        verbose_name='Ocorrências',
        default=''
    )

    status = models.PositiveSmallIntegerField(
        db_index=True,
        choices=SR.choices,
        help_text='Status da requisição',
        verbose_name='Status',
        default=SR.REQUERIDO,
    )

    class Meta:
        verbose_name = 'requisição'
        verbose_name_plural = 'requisições'
        ordering = ('-data', '-hora_inicio')

    def __str__(self):
        return '{0} - {1} - {2}'.format(str(self.id), self.laboratorio.codigo, self.data.strftime("%d/%m/%Y"))

    def get_absolute_url(self):
        return reverse('requisicao_detalhes', args=[self.id])

    @property
    def tipo_atividade_string(self):
        return self.TIPOS_DE_ATIVIDADE(self.tipo_atividade).label

    @property
    def status_string(self):
        return SR(self.status).label

    @property
    def status_aprovavel(self):
        if self.status in (SR.REQUERIDO, ):
            return True
        return False

    @property
    def status_cancelavel(self):
        if self.status in (SR.REQUERIDO, SR.APROVADO, SR.APROVADO_PARCIAL):
            return True
        return False

    @property
    def status_rejeitavel(self):
        if self.status in (SR.REQUERIDO, SR.APROVADO, SR.APROVADO_PARCIAL):
            return True
        return False

    @property
    def status_atendivel(self):
        if self.status in (SR.APROVADO, SR.APROVADO_PARCIAL):
            return True
        return False

    @property
    def status_finalizavel(self):
        if self.status in (SR.ATENDIDO, ):
            return True
        return False

    @property
    def status_pos_aprovacao(self):
        if self.status in (SR.APROVADO, SR.APROVADO_PARCIAL, SR.ATENDIDO, SR.FINALIZADO):
            return True
        return False

    @property
    def status_pos_devolucao(self):
        if self.status in (SR.ATENDIDO, SR.FINALIZADO):
            return True
        return False

    @property
    def status_class(self):
        if self.status == SR.REQUERIDO:
            return 'success'
        if self.status == SR.APROVADO:
            return 'primary'
        if self.status == SR.APROVADO_PARCIAL:
            return 'info'
        if self.status == SR.ATENDIDO:
            return 'warning'
        if self.status == SR.REJEITADO:
            return 'danger'
        if self.status == SR.FINALIZADO:
            return 'secondary'
        if self.status == SR.CANCELADO:
            return 'ligth'
        return 'ligth'

    @property
    def itens_requisitados(self):
        return ItemRequisitado.objects.filter(requisicao=self)

    @itens_requisitados.setter
    def itens_requisitados(self, value):
        '''Ler a informação de um json e adicona a tabela
        itens requisitados'''
        if value:
            for ir in ItemRequisitado.json_to_list(self, value):
                ir.save()

    @property
    def itens_nao_solicitados(self):
        todos_itens = Item.objects.filter(
            status=STATUS_BASICO.ATIVO, escopo=self.escopo)
        return [i for i in todos_itens if i not in self.itens.all()]

    def atualizar_itens(self, value, incluir_novos=True):
        '''Recebe um json de itens aprovados/devolvidos e mesclas os itens solicitados'''
        for ia in ItemRequisitado.json_to_list(self, value):
            ItemRequisitado.atualizar(ia, incluir_se_nao_existe=incluir_novos)

    @property
    def aprovado_igual_a_solicitado(self):
        for ir in self.itens_requisitados:
            if ir.solicitado and ir.solicitado > ir.aprovado:
                return False
        return True

    @property
    def qt_itens(self):
        return ItemRequisitado.objects.filter(requisicao=self).count()

    @property
    def historico(self):
        return Auditoria.get_descricoes(**{"noque": Auditoria.MODELOS.REQUISICAO, "noqual": self.id})


class ItemRequisitado(models.Model):
    requisicao = models.ForeignKey(
        "Requisicao",
        verbose_name=_("Requisicao Contido"),
        on_delete=models.PROTECT,
        related_name='ItensRequisitados')

    item = models.ForeignKey(
        "Item",
        verbose_name=_("Item Requisitado"),
        on_delete=models.PROTECT,
        related_name='ItensRequisitados')

    _qt_solicitado = models.PositiveSmallIntegerField(
        help_text='Quantidade solicitada',
        verbose_name='Quantidade solicitada',
        default=0)

    _qt_estoque = models.PositiveSmallIntegerField(
        help_text='Quantidade em estoque quanto solicitado',
        verbose_name='Estoque no requisicão',
        default=0)

    _qt_aprovado = models.PositiveSmallIntegerField(
        help_text='Quantidade aprovada',
        verbose_name='Quantidade aprovada',
        default=0)

    _qt_devolvido = models.PositiveSmallIntegerField(
        verbose_name='Quantidade devolvida',
        default=0)

    c_aprovado = models.TextField(
        verbose_name="Comentário deixado na aprovação",
        default='')

    c_devolvido = models.TextField(
        verbose_name="Comentário deixado na devolução",
        default='')

    class Meta:
        unique_together = ("item", "requisicao")

    @staticmethod
    def getItem(requisicao,
                id=0,
                solicitado=0,
                estoque=0,
                aprovado=0,
                devolvido=0,
                c_aprovado='',
                c_devolvido=''):

        r = ItemRequisitado()
        r.requisicao = requisicao
        if id == 0:
            r.item = Item()
        else:
            r.item = Item.objects.get(id=id)
        r.solicitado = solicitado
        r.estoque = estoque
        r.aprovado = aprovado
        r.devolvido = devolvido
        r.c_aprovado = c_aprovado
        r.c_devolvido = c_devolvido

        return r

    def __eq__(self, outro_item):
        return self.item.id == outro_item.item.id and self.requisicao.id == outro_item.requisicao.id

    @property
    def solicitado(self):
        return self._qt_solicitado

    @solicitado.setter
    def solicitado(self, value):
        try:
            self._qt_solicitado = int(value)
        except ValueError:
            self._qt_solicitado = 0

    @property
    def estoque(self):
        return self._qt_estoque

    @estoque.setter
    def estoque(self, value):
        try:
            self._qt_estoque = int(value)
        except ValueError:
            self._qt_estoque = 0

    @property
    def aprovado(self):
        return self._qt_aprovado

    @aprovado.setter
    def aprovado(self, value):
        try:
            self._qt_aprovado = int(value)
        except ValueError:
            self._qt_aprovado = 0

    @property
    def devolvido(self):
        return self._qt_devolvido

    @devolvido.setter
    def devolvido(self, value):
        try:
            self._qt_devolvido = int(value)
        except ValueError:
            self._qt_devolvido = 0

    def __str__(self):
        return self.item.nome + ' -  ' + str(self.solicitado)

    @staticmethod
    def json_to_list(requisicao, list_json):
        '''Recebe uma lista Json e retorna uma lista de ItensRequisitados'''
        if list_json:
            return [ItemRequisitado.getItem(requisicao, **i) for i in json.loads(list_json)]

    @staticmethod
    def atualizar(item_r, incluir_se_nao_existe=True):
        try:
            atualizado = ItemRequisitado.objects.get(
                requisicao=item_r.requisicao,
                item=item_r.item)
        except ItemRequisitado.DoesNotExist:
            if incluir_se_nao_existe:
                atualizado = ItemRequisitado.getItem(
                    item_r.requisicao, id=item_r.item.id)
            else:
                return

        atualizado.solicitado += item_r.solicitado
        atualizado.estoque += item_r.estoque
        atualizado.aprovado += item_r.aprovado
        atualizado.c_aprovado += item_r.c_aprovado
        atualizado.devolvido += item_r.devolvido
        atualizado.c_devolvido += item_r.c_devolvido

        atualizado.save()
        return atualizado


class HistoricoEstoque(models.Model):
    item = models.ForeignKey(
        "Item",
        verbose_name=_("Item"),
        on_delete=models.PROTECT,
        related_name="historicosEstoque",
        limit_choices_to={"status": STATUS_BASICO.ATIVO,
                          "tipo": Item.TIPOS_DE_ITENS.MATERIAL}
    )
    data_hora = models.DateTimeField(
        _("Data/Hora"), auto_now_add=True)

    movimentacao = models.IntegerField(_("quantidade"))

    estoque_anterior = models.IntegerField(
        _("estoque anterior"),
        default=0
    )

    requisicao = models.ForeignKey(
        "Requisicao",
        verbose_name=_("requisição"),
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name="historicosEstoque")

    descricao = models.TextField(_("descrição"))

    class Meta:
        verbose_name = 'Evento de Estoque'
        verbose_name_plural = 'Histórico do Estoque de Materias'
        ordering = ('-data_hora',)

    def save(self, *args, **kwargs):
        if self.movimentacao != 0:
            self.estoque_anterior = self.item.estoque
            self.item.estoque += self.movimentacao
            super(HistoricoEstoque, self).save(*args, **kwargs)

    def __str__(self):
        return '{0}-{1}'.format(str(self.id), self.item)

    def quantidade(self):
        return str(self.movimentacao) + self.item.unidade.codigo


class Cesta(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("usuario"),
        on_delete=models.PROTECT,
        related_name="cestas")

    nome = models.CharField(
        max_length=50
    )

    itens = models.TextField()

    escopo = models.ForeignKey("Escopo", verbose_name=_(
        "escopo"), on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

    def url_delete(self):
        return reverse('cestas_salvas', args=[self.id])

    def qt_itens(self):
        qt = 0
        try:
            qt = len(json.loads(self.itens))
        except Exception as e:
            print(self.itens)
            print(e)
            qt = 0

        return qt

    def itens_to_load(self):
        #id, nome, descricao, tipo, unidade, quantidade, estoque
        itens = []
        if self.itens:
            try:
                for i in json.loads(self.itens):
                    try:
                        item = Item.objects.get(
                            id=i['id'], status=STATUS_BASICO.ATIVO)

                        i_json = {
                            "id": item.id,
                            "nome": item.nome,
                            "descricao": item.descricao,
                            "tipo": item.tipo,
                            "unidade": item.unidade.codigo,
                            "quantidade": i['quantidade'],
                            "estoque": item.estoque
                        }

                        itens.append(i_json)
                    except Item.DoesNotExist:
                        pass
            except Exception:
                pass
        return json.dumps(itens)


class Auditoria(models.Model):
    quem = models.ForeignKey(
        "Usuario",
        verbose_name=_("Quem realizou a acão"),
        on_delete=models.PROTECT)

    class MODELOS(models.IntegerChoices):
        USUARIO = 1
        LABORATORIO = 2
        UNIDADE = 3
        ITEM = 4
        FERRAMENTA = 5
        ESTOQUEMATERIAL = 6
        REQUISICAO = 7
        ITEMREQUISITADO = 8

    noque = models.IntegerField(
        verbose_name=_("Modelo Envolvido"),
        choices=MODELOS.choices)

    noqual = models.IntegerField(
        verbose_name=_("Id do Modelo envolvido"),
        choices=MODELOS.choices)

    quando = models.DateTimeField(
        verbose_name=("quando o evento ocorreu"),
        auto_now_add=True)

    class ACOES(models.IntegerChoices):
        CRIAR_REQUISICAO = 1
        ADD_COMENTARIO = 2
        CANCELAR_REQUISICAO = 3
        FINALIZAR_REQUISICAO = 4
        REJEITAR_REQUISICAO = 5
        APROVAR_REQUISICAO = 6
        APROVAR_PARCIALMENTE_REQUISICAO = 7
        ATENDER_REQUISICAO = 8
        MODIFICAR_DADOS_PESSOAIS = 9

    oque = models.IntegerField(
        verbose_name=_("Ação Realizada"),
        choices=ACOES.choices)

    @property
    def get_quando(self):
        return self.quando.strftime(
            "%d/%m/%Y às %H:%M:%S")

    @property
    def get_descricao(self):
        if self.oque == self.ACOES.CRIAR_REQUISICAO:
            return '''CRIADA por {0} 
            em {1}'''.format(self.quem, self.get_quando)
        if self.oque == self.ACOES.ADD_COMENTARIO:
            return '''COMENTÁRIO ADICIONADO por {0} 
            em {1}'''.format(self.quem, self.get_quando)
        if self.oque == self.ACOES.CANCELAR_REQUISICAO:
            return '''CANCELADA por {0} 
            em {1}'''.format(self.quem, self.get_quando)
        if self.oque == self.ACOES.FINALIZAR_REQUISICAO:
            return '''FINALIZADA por {0} 
            em {1}'''.format(self.quem, self.get_quando)

        if self.oque == self.ACOES.REJEITAR_REQUISICAO:
            return '''REJEITADA por {0} 
            em {1}'''.format(self.quem, self.get_quando)

        if self.oque == self.ACOES.APROVAR_REQUISICAO:
            return '''APROVADA por {0} 
            em {1}'''.format(self.quem, self.get_quando)

        if self.oque == self.ACOES.APROVAR_PARCIALMENTE_REQUISICAO:
            return '''APROVADA PARCIALMENTE por {0} 
            em {1}'''.format(self.quem, self.get_quando)

        if self.oque == self.ACOES.ATENDER_REQUISICAO:
            return '''REGISTRADA COMO ATENDIDA por {0} 
            em {1}'''.format(self.quem, self.get_quando)

        if self.oque == self.MODIFICAR_DADOS_PESSOAIS:
            return '''DADOS PESSOAIS modificado em {0}'''.format(self.get_quando)

    @staticmethod
    def get_descricoes(**kwargs):
        return [a.get_descricao for a in Auditoria.objects.filter(**kwargs)]


class ConfigLab(models.Model):
    class CONFIG (models.IntegerChoices):
        TAMANHO_MAXIMO_ROTEIRO = 1, _(
            'Tamanho máximo permitido para o envio do roteiro em MB.')
        PERMITIR_ESTOURAR_ESTOQUE = 2, _('#Permitir estourar o estoque.')
        PERMITIR_SOBREPOSICAO = 3, _(
            "#Permitir sobreposição de requisições (mesma data/hora e local)")
        PERMITIR_REQUISICAO_DOMINGO = 4, _(
            "#Permitir requisições aos domingos")
        PERMITIR_REQUISICAO_SABADO = 5, _("#Permitir requisições aos sábados")
        PERMITIR_REQUISICAO_FERIADO = 6, _("#Permitir requisições em feriados")
        HORARIO_MINIMO_REQUISICAO = 7, _(
            '#Horário mínimo para requisião(HHMM)')
        HORARIO_MAXIMO_REQUISICAO = 8, _(
            '#Horário máximo para requisião(HHMM)')
        ENVIAR_EMAIL_PROFESSOR = 9, _('#Enviar e-mail aos professores')
        ENVIAR_EMAIL_REQUISITANTE = 10, _('#Enviar e-mail aos requisitantes')
        ENVIAR_EMAIL_TECNICOS = 11, _('#Enviar e-mail aos técnicos')
        ANTECEDENCIA_MINIMA_REQUISICAO = 12, _(
            '#Antecedência mínima da requisição (Em horas)')

    configuracao = models.IntegerField(
        verbose_name=_("configuração"),
        unique=True,
        blank=False,
        null=False,
        choices=CONFIG.choices
    )
    valor = models.IntegerField(
        verbose_name=_("valor")
    )

    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'
        ordering = ('configuracao',)

    def __str__(self):
        return str(self.CONFIG(self.configuracao).label) + "Valor Definido = %s" % str(self.valor)

    def save(self, *args, **kwargs):
        if self.CONFIG(self.configuracao).label[:1] != 'W!':
            super(ConfigLab, self).save(*args, **kwargs)

    @staticmethod
    def get_config_default(value):
        default_value = {
            '1': 2,  # Tamanho máximo do arquivo de roteiro
            '2': 1,  # Permitir estourar o estoque
            '3': 1,  # Permitir sobreposição
        }
        return default_value.get(str(value), 0)

    @staticmethod
    def get_value(value):
        try:
            return ConfigLab.objects.get(configuracao=value).valor
        except ConfigLab.DoesNotExist:
            return ConfigLab.get_config_default(value)


class Aviso(models.Model):
    escopo = models.ForeignKey("Escopo", verbose_name=_(
        "escopo"), on_delete=models.CASCADE,blank=True, null=True)
    titulo = models.CharField(_("título"), max_length=50)
    mensagem = models.TextField(_("menssagem"))
    inicio = models.DateTimeField(
        _("início de vigência"), auto_now=False, auto_now_add=False)
    fim = models.DateTimeField(
        _("fim de vigência"), auto_now=False, auto_now_add=False)
    importante = models.BooleanField(_("em destaque"))
    status = models.PositiveSmallIntegerField(
        _("status"),
        choices=STATUS_BASICO.choices,
        default=STATUS_BASICO.ATIVO
    )

    class Meta:
        verbose_name = 'Aviso'
        verbose_name_plural = 'Avisos'
        ordering = ('-importante', 'inicio', 'fim')

    def __str__(self):
        return self.titulo


class Escopo(models.Model):
    nome = models.CharField(_("nome"), max_length=50)
    tecnicos = models.ManyToManyField("Usuario", verbose_name=_("técnicos"),
                                      limit_choices_to={
                                          'is_active': True, 'is_staff': True}
                                      )
    status = models.PositiveSmallIntegerField(
        _("status"),
        choices=STATUS_BASICO.choices,
        default=STATUS_BASICO.ATIVO
    )

    class Meta:
        verbose_name = 'Escopo'
        verbose_name_plural = 'Escopos'
        ordering = ('nome',)

    def __str__(self):
        return self.nome

    @property
    def responsaveis(self):
        return list(self.tecnicos.all())
