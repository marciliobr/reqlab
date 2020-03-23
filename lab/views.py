import datetime
import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import InvalidPage, Paginator
from django.http import (HttpRequest, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import (get_list_or_404, get_object_or_404, redirect,
                              render, reverse)
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from decouple import config

from .forms import *
from .models import SR, SB
from .models import Auditoria as Aud
from .models import (Aviso, Cesta, ConfigLab, Escopo, EstoqueMaterial, Ferramenta,
                     Item, Requisicao, Usuario)
from .tasks import enviar_email
from .utils import ReqCalendario

ITEMS_PER_PAGE = config("ITEMS_PER_PAGE", default=5)

ESCOPO_ID_REF = 'escopo_id'
ESCOPO_NOME_REF = 'escopo_nome'


def ESCOPO_ID(request): return request.session.get(ESCOPO_ID_REF, 0)


def ESCOPO(request): return get_object_or_404(
    Escopo, status=SB.ATIVO, id=ESCOPO_ID(request))


def home(request):
    assert isinstance(request, HttpRequest)
    limpar_cesta = False
    if request.user.is_authenticated:
        new_escopo = request.GET.get('escopo', 0)
        if new_escopo:
            escopo = get_object_or_404(
                Escopo, id=new_escopo, status=SB.ATIVO)
            request.session[ESCOPO_ID_REF] = escopo.id
            request.session[ESCOPO_NOME_REF] = escopo.nome
            limpar_cesta = True

        if not ESCOPO_ID(request):
            escopo_default = request.user.escopo_default
            if escopo_default and escopo_default.status == SB.ATIVO:
                request.session[ESCOPO_ID_REF] = escopo_default.id
                request.session[ESCOPO_NOME_REF] = escopo_default.nome
            else:
                return redirect('edit_user')

        if not request.user.email:
            return redirect('edit_user')

    agora = datetime.datetime.now()
    
    quadro_avisos = list(Aviso.objects.filter(
        status=SB.ATIVO, inicio__lte=agora, fim__gte=agora, escopo__id = ESCOPO_ID(request)))
    quadro_avisos +=  list(Aviso.objects.filter(
        status=SB.ATIVO, inicio__lte=agora, fim__gte=agora, escopo=None))
    
    return render(request, 'lab/index.html', {"quadro_avisos": quadro_avisos, 'limpar_cesta': limpar_cesta})


@login_required(login_url='/login/')
def form_requisicao(request):
    if request.method == 'POST':
        form = RequisicaoForm(data=request.POST, files=request.FILES,
                              escopo_id=ESCOPO_ID(request), usuario=request.user)
        if form.is_valid():
            requisicao = form.save(commit=False)

            # TODO - Adicionar tratamento de erros
            requisicao.save()
            requisicao.itens_requisitados = requisicao.itens_json

            # Auditoria
            Aud(quem=request.user,
                noque=Aud.MODELOS.REQUISICAO,
                noqual=requisicao.id,
                oque=Aud.ACOES.CRIAR_REQUISICAO).save()

            # E-mail

            enviar_email.delay(subject="Nova Requisição Cadastrada",
                               message="Uma nova requisição foi cadastrada.",
                               mstype=1,
                               recipients=[request.user.id,
                                           requisicao.professor.id],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )

            return redirect('lista_requisicoes')
    else:
        if request.user.is_staff:
            requisicao = Requisicao(escopo=ESCOPO(request))
        else:
            requisicao = Requisicao(professor=request.user, escopo=ESCOPO(request))
        form = RequisicaoForm(instance=requisicao,
                              escopo_id=ESCOPO_ID(request), usuario=request.user)

    return render(request, 'lab/requisicao.html', {
        'form': form})


@login_required(login_url='/login/')
def edit_user(request):
    if request.method == 'POST':
        form = EditUserForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            email = str(request.user.email)
            if email and email != usuario.email:
                enviar_email.delay(subject="Dados cadastrais alterados",
                                   message="Seus dados cadastrais foram alterados no REQLAB",
                                   mstype=2,
                                   statics=[email, ],
                                   object_id=int(request.user.id)
                                   )
            request.user.first_name = usuario.first_name
            request.user.last_name = usuario.last_name
            request.user.email = usuario.email
            request.user.escopo_default = usuario.escopo_default

            # TODO - Adicionar tratamento de erros
            request.user.save()
            Aud(quem=request.user,
                noque=Aud.MODELOS.USUARIO,
                noqual=request.user.id,
                oque=Aud.ACOES.MODIFICAR_DADOS_PESSOAIS).save()

            enviar_email.delay(subject="Dados cadastrais alterados",
                               message="Seus dados cadastrais foram alterados no REQLAB",
                               mstype=2,
                               recipients=[request.user.id],
                               object_id=request.user.id
                               )

            return redirect('home')
    else:
        form = EditUserForm(instance=request.user)

    return render(request, 'lab/edit_user.html', {
        'form': form})


@login_required(login_url='/login/')
def cesta(request):
    assert isinstance(request, HttpRequest)
    itens = Item.objects.filter(
        status=SB.ATIVO, escopo__id=ESCOPO_ID(request))  # ativos
    return render(request, "lab/cesta.html", {"itens": itens})


@login_required(login_url='/login/')
def lista_requisicoes(request):
    assert isinstance(request, HttpRequest)
    pagina = request.GET.get('page', 1)
    paginator = Paginator(request.user.requisicoes.filter(escopo__id=ESCOPO_ID(request)), ITEMS_PER_PAGE)
    try:
        requisicoes = paginator.page(pagina)
    except InvalidPage:
        requisicoes = paginator.page(1)

    return render(
        request,
        'lab/lista_requisicoes.html',
        {
            'requisicoes': requisicoes,
            'mostrar': True
        }
    )


@staff_member_required(login_url='/login/')
def gerir_requisicoes(request):
    assert isinstance(request, HttpRequest)
    pagina = request.GET.get('page', 1)
    filtro = request.GET.get('filter', 1)
    status = (SR.REQUERIDO,)
    if filtro == '2':  # Aprovadados
        status = (SR.APROVADO, SR.APROVADO_PARCIAL)
    elif filtro == '3':  # Atendidos
        status = (SR.ATENDIDO,)
    elif filtro == '4':  # Encerrados
        status = (SR.CANCELADO, SR.FINALIZADO, SR.REJEITADO)
    else:
        filtro = '1'

    paginator = Paginator(Requisicao.objects.filter(
        status__in=status, escopo_id=ESCOPO_ID(request)), ITEMS_PER_PAGE)
    total = paginator.count
    try:
        requisicoes = paginator.page(pagina)
    except InvalidPage:
        requisicoes = paginator.page(1)

    return render(
        request,
        'lab/gerir_requisicoes.html',
        {
            'usuario': request.user,
            'requisicoes': requisicoes,
            'total_requisicoes': total,
            'filtro': str(filtro),
        }
    )


@login_required(login_url='/login/')
def registrar_cancelamento_requisicao(request):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        form = FormCancelamentoRequisicao(request.POST)
        if form.is_valid():
            id = form.data['id']
            id_confirmacao = form.data['id_confirmacao']
            requisicao = get_object_or_404(Requisicao, pk=id)

            if id != id_confirmacao:
                return HttpResponse('O ID informado não confere!')

            if (not requisicao.status_cancelavel):  # Verificando o status do objeto
                return HttpResponse('O status atual da requisicao não permite cancelamento!')

            # Verificando se o usuario é o professor da disciplina
            if request.user != requisicao.professor:
                return HttpResponse(
                    '''Você não é o professor da disciplina desta requisição,
                    apenas {0} poderá resgistrar seu cancelamento!'''.format(requisicao.professor.nome))

            #  Se a requisicação já passou por aprovação, então o estoque deverá ser subido
            subir_estoque = not requisicao.status_aprovavel
            requisicao.status = SR.CANCELADO
            try:
                requisicao.save()
                if subir_estoque:
                    Item.baixar_estoque(requisicao=requisicao, desfazer=True)

            except Exception as erro:
                return HttpResponse(
                    '''Ocorreu um erro inesperado! Erro:{0}'''.format(erro)
                )

            Aud(quem=request.user,
                noque=Aud.MODELOS.REQUISICAO,
                noqual=requisicao.id,
                oque=Aud.ACOES.CANCELAR_REQUISICAO).save()

            enviar_email.delay(subject="Requisição Cancelada",
                               message="A Requisição foi cancelada!",
                               mstype=1,
                               recipients=[request.user.id,
                                           requisicao.professor.id],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )

            return HttpResponse('1')


@login_required(login_url='/login/')
def adicionar_observacao(request):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        form = FormAdicionarObservacao(request.POST)
        if form.is_valid():
            id = form.data['id']
            if not form.data['observacao'].strip():
                return HttpResponse('Informe uma observação!')

            observacao = ''' => (Em {0} - por {2}): {1}'''.format(datetime.datetime.now(
            ).strftime("%d/%m/%Y às %H:%M:%S"), form.data['observacao'], request.user.username)
            requisicao = get_object_or_404(Requisicao, pk=id)

            # Verificando o status do objeto
            if (not requisicao.status_cancelavel):
                return HttpResponse('O status atual da requisicao não permite adicionar observações!')

            # Verificando se o usuario é o professor da disciplina
            if request.user != requisicao.professor:
                return HttpResponse(
                    '''Você não é o professor da disciplina desta requisição,
                    apenas {0} poderá adicionar observações!'''.format(requisicao.professor.nome))

            # Adiciona ocorrencia
            requisicao.observacoes += observacao
            try:
                requisicao.save()
            except Exception as erro:
                return HttpResponse(
                    '''Ocorreu um erro inesperado! Erro:{0}'''.format(erro)
                )

            Aud(quem=request.user,
                noque=Aud.MODELOS.REQUISICAO,
                noqual=requisicao.id,
                oque=Aud.ACOES.ADD_COMENTARIO).save()

            enviar_email.delay(subject="Nova observação adicionada à requisição",
                               message="OBSERVAÇÃO ADICIONADA: {0}".format(
                                   observacao),
                               mstype=1,
                               recipients=[request.user.id,
                                           requisicao.professor.id],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )

            return HttpResponse('1')


@login_required(login_url='/login/')
def finalizacao(request):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        form = FormFinalizacao(request.POST)
        if form.is_valid():
            id = form.data['id']
            if form.data['ocorrencia'].strip():
                ocorrencia = '''  (OCORRÊNCIA NA FINALIZAÇÃO) Em {0} - por {2}): {1}'''.format(datetime.datetime.now().strftime(
                    "%d/%m/%Y às %H:%M:%S"), form.data['ocorrencia'], request.user.username)
            else:
                ocorrencia = ''

            requisicao = get_object_or_404(Requisicao, pk=id)

            # Verificando o status do objeto
            if (not requisicao.status_finalizavel):
                return HttpResponse('O status atual da requisicao não permite finaliza-la!')

            # Verificando se o usuario é o professor da disciplina

            if not request.user.is_staff:
                if request.user != requisicao.professor:
                    return HttpResponse(
                        '''Você não é o professor da disciplina desta requisição,
                        apenas {0} poderá finaliza-la!'''.format(requisicao.professor.nome))

            # Adiciona ocorrencia
            requisicao.ocorrencias += ocorrencia
            requisicao.status = SR.FINALIZADO

            try:
                requisicao.save()
            except Exception as erro:
                return HttpResponse(
                    '''Ocorreu um erro inesperado! Erro:{0}'''.format(erro)
                )
            Aud(quem=request.user,
                noque=Aud.MODELOS.REQUISICAO,
                noqual=requisicao.id,
                oque=Aud.ACOES.FINALIZAR_REQUISICAO).save()

            enviar_email.delay(subject="Requisição Finalizada",
                               message="A Requisição foi FINALIZADA!",
                               mstype=1,
                               recipients=[request.user.id,
                                           requisicao.professor.id],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )

            return HttpResponse('1')


@staff_member_required(login_url='/login/')
def rejeicao(request):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        form = FormRejeicao(request.POST)
        if form.is_valid():
            id = form.data['id']
            if form.data['ocorrencia'].strip():
                ocorrencia = '''   (OCORRÊNCIA DE REJEIÇÃO - Em {0} - por {2}): {1}'''.format(datetime.datetime.now().strftime(
                    "%d/%m/%Y às %H:%M:%S"), form.data['ocorrencia'], request.user.username)
            else:
                ocorrencia = ''

            requisicao = get_object_or_404(Requisicao, pk=id)

            # Verificando o status do objeto
            if (not requisicao.status_rejeitavel):
                return HttpResponse('O status atual da requisicao não permite rejeita-la!')

            # Adiciona ocorrencia
            requisicao.ocorrencias += ocorrencia
            requisicao.status = SR.REJEITADO

            #  Se a requisicação já passou por aprovação, então o estoque deverá ser subido
            subir_estoque = not requisicao.status_aprovavel
            try:
                requisicao.save()
                if subir_estoque:
                    Item.baixar_estoque(requisicao=requisicao, desfazer=True)
            except Exception as erro:
                return HttpResponse(
                    '''Ocorreu um erro inesperado! Erro:{0}'''.format(erro)
                )

            Aud(quem=request.user,
                noque=Aud.MODELOS.REQUISICAO,
                noqual=requisicao.id,
                oque=Aud.ACOES.REJEITAR_REQUISICAO).save()

            enviar_email.delay(subject="Requisição Rejeitada",
                               message="A Requisição foi REJEITADA!",
                               mstype=1,
                               recipients=[request.user.id,
                                           requisicao.professor.id],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )

            return HttpResponse('1')


@staff_member_required(login_url='/login/')
def requisicao_aprovar(request):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        form = FormAprovacao(request.POST)
        if form.is_valid():
            id = form.data['id']
            if form.data['observacao'].strip():
                ocorrencia = '''   (RESALVAS NA APROVAÇÃO: Em {0} - por {2}): {1}'''.format(
                    datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
                    form.data['observacao'],
                    request.user.username)
            else:
                ocorrencia = ''

            requisicao = get_object_or_404(Requisicao, id=id)

            # Verificando o status do objeto
            if (not requisicao.status_aprovavel):
                return HttpResponse('O status atual da requisicao não permite esta ação!')

            # TODO Verificar se a data do evento já não passou

            # Adiciona ocorrencia
            if ocorrencia:
                requisicao.ocorrencias += ocorrencia

            try:
                str_aprovados = form.data['itens_aprovados']
                if str_aprovados:
                    requisicao.atualizar_itens(str_aprovados)
                integralmente = requisicao.aprovado_igual_a_solicitado
                requisicao.status = SR.APROVADO if integralmente else SR.APROVADO_PARCIAL
                requisicao.save()
                Item.baixar_estoque(requisicao)
            except Exception as erro:
                return HttpResponse(
                    '''Ocorreu um erro inesperado! Erro:{0}'''.format(erro)
                )
            Aud(quem=request.user,
                noque=Aud.MODELOS.REQUISICAO,
                noqual=requisicao.id,
                oque=Aud.ACOES.APROVAR_REQUISICAO if integralmente else Aud.ACOES.APROVAR_PARCIALMENTE_REQUISICAO).save()

            enviar_email.delay(subject="Requisição Aprovada" if integralmente else "Requisição Aprovada Parcialmente",
                               message="A Requisição foi APROVADA!" if integralmente else "A Requisição for APROVADA, mas houve revisão dos itens solicitados.",
                               mstype=1,
                               recipients=[requisicao.professor.id],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )

            return redirect(requisicao)


@staff_member_required(login_url='/login/')
def requisicao_devolver(request):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        form = FormDevolucao(request.POST)
        if form.is_valid():
            id = form.data['id']
            if form.data['observacao'].strip():
                ocorrencia = '''  (OCORRÊNICA NA DEVOLUÇÃO: Em {0} - por {2}): {1}'''.format(
                    datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
                    form.data['observacao'],
                    request.user.username)
            else:
                ocorrencia = ''

            requisicao = get_object_or_404(Requisicao, id=id)

            # Verificando o status do objeto
            if (not requisicao.status_atendivel):
                return HttpResponse('O status atual da requisicao não permite esta ação!')

            # Adiciona ocorrencia
            if ocorrencia:
                requisicao.ocorrencias += ocorrencia

            try:
                str_devolvidos = form.data['itens_devolvidos']
                if str_devolvidos:
                    requisicao.atualizar_itens(
                        str_devolvidos, incluir_novos=False)
                requisicao.status = SR.ATENDIDO
                requisicao.save()
                Item.baixar_estoque(requisicao=requisicao, devolucao=True)
            except Exception as erro:
                # TODO Adicionar uma página para destino
                return HttpResponse(
                    '''Ocorreu um erro inesperado! Erro:{0}'''.format(erro)
                )

            Aud(quem=request.user,
                noque=Aud.MODELOS.REQUISICAO,
                noqual=requisicao.id,
                oque=Aud.ACOES.ATENDER_REQUISICAO).save()

            enviar_email.delay(subject="Requisição Pendente de Finalização",
                               message="A Requisição for marcada como ATENDIDA, você deve registra a finalização da mesma!",
                               mstype=1,
                               recipients=[requisicao.professor.id],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )
            enviar_email.delay(subject="Requisição Atendida",
                               message="A Requisição for marcada como ATENDIDA!",
                               mstype=1,
                               recipients=[],
                               id_escopo=ESCOPO_ID(request),
                               object_id=requisicao.id
                               )

            return redirect(requisicao)


@login_required(login_url='/login/')
def calendario(request, ano=None, mes=None):
    assert isinstance(request, HttpRequest)

    d = datetime.date.today()
    ano = ano or d.year
    mes = mes or d.month
    requisicoes = Requisicao.objects.filter(
        data__month=mes, data__year=ano, escopo__id=ESCOPO_ID(request))

    cal = ReqCalendario(requisicoes, request.user)
    html_calendar = cal.formatmonth(ano, mes, withyear=True)

    return render(
        request,
        'lab/calendario.html',
        {
            'calendario': mark_safe(html_calendar),
            'ano_proximo': ano + 1 if (mes + 1) > 12 else ano,
            'mes_proximo': 1 if (mes + 1) > 12 else mes + 1,
            'ano_anterior': ano - 1 if (mes - 1) < 1 else ano,
            'mes_anterior': 12 if (mes - 1) < 1 else mes - 1,
        }
    )


@login_required(login_url='/login/')
def requisicao_detalhes(request, id=0):
    assert isinstance(request, HttpRequest)
    requisicao = get_object_or_404(Requisicao, id=id)
    data = {
        'is_to_print': request.GET.get('print', False) == 'True',
        'requisicao': requisicao,
        'mostrar': request.user.is_staff or requisicao.professor == request.user
    }

    return render(request, 'lab/requisicao_detalhes.html', data)


@staff_member_required(login_url='/login/')
def cesta_revisao(request, id=0):
    assert isinstance(request, HttpRequest)
    requisicao = get_object_or_404(Requisicao, id=id)
    if not requisicao.status_aprovavel:
        return HttpResponseRedirect(reverse('requisicao_detalhes', args=[id]))
    data = {
        'requisicao': requisicao
    }
    return render(request, 'lab/cesta_revisao.html', data)


@staff_member_required(login_url='/login/')
def cesta_devolucao(request, id=0):
    assert isinstance(request, HttpRequest)
    requisicao = get_object_or_404(Requisicao, id=id)
    if not Requisicao.status_atendivel:
        return HttpResponseRedirect(reverse('requisicao_detalhes', args=[id]))
    data = {
        'requisicao': requisicao
    }

    return render(request, 'lab/cesta_devolucao.html', data)


@login_required(login_url='/login/')
def cestas_salvas(request, id=0):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        form = FormSalvarCesta(request.POST)
        if form.is_valid():
            nome = form.data['nome'].strip()
            itens = form.data['itens'].strip()

            if not itens:
                return HttpResponse('Não faz sentido salvar uma cesta vazia!')

            cesta = Cesta(usuario=request.user)
            cesta.nome = nome
            cesta.itens = itens
            cesta.escopo = ESCOPO(request)

            try:
                cesta.save()
            except Exception as erro:
                return HttpResponse(
                    '''Ocorreu um erro inesperado! Erro:{0}'''.format(erro)
                )

            return HttpResponse('1')

    if request.method == 'GET':
        try:
            cesta = Cesta.objects.get(id=id)
            if cesta.usuario != request.user:
                return HttpResponse("Apenas quem criou a cesta pode excluí-la", status=401)
            cesta.delete()
            return HttpResponse("Cesta excluída!", status=200)
        except Exception as e:
            return HttpResponse(e, status=400)


@staff_member_required(login_url='/login/')
def reports_home(request):
    assert isinstance(request, HttpRequest)
    return render(request, 'lab/reports/reports_home.html')


@staff_member_required(login_url='/login/')
def report_estoque_geral(request):
    assert isinstance(request, HttpRequest)
    consumo = request.GET.get('consumo', False) == 'True'
    permanente = request.GET.get('permanente', False) == 'True'
    if consumo == permanente:
        consumo, permanente = True, True
    data = {
        'is_to_print': request.GET.get('print', False) == 'True',
        'itens_consumo': Item.objects.filter(status=SB.ATIVO, tipo=Item.ITEM_TIPO.MATERIAL, escopo__id=ESCOPO_ID(request)) if consumo else [],
        'itens_permanente': Item.objects.filter(status=SB.ATIVO, tipo=Item.ITEM_TIPO.FERRAMENTA, escopo__id=ESCOPO_ID(request)) if permanente else [],
        'mostrar_consumo':consumo,
        'mostrar_permanente':permanente
    }
    return render(request, 'lab/reports/estoque_geral.html', data)
