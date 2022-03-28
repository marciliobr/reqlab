import datetime

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import ConfigLab, Laboratorio, Requisicao, Usuario, Escopo, SB


def list_admin():
    try:
        return render_to_string(
            template_name="lab/includes/nao_autorizado.html",
            context={"escopos": Escopo.objects.filter(status= SB.ATIVO)}
        )
    except Exception:
        return ''


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=10,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'Mátricula (SIAPE)'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder': 'Senha do SUAPE'}))

    error_messages = {
        'invalid_login': _(
            "Digite uma matrícula e senha corretas."
            " Observe que os dois campos podem fazer distinção entre maiúsculas e minúsculas."
            " ATENÇÃO - Como esta autenticação depende do correto funcinamento do SUAP, "
            " vefirique se o SUAP está funcionando corretamente antes de tentar novamente."
        ),
        'inactive': mark_safe('Esta conta não está ativa!' + list_admin()),
    }


def file_size(value):
    limite = ConfigLab.get_value(ConfigLab.CONFIG.TAMANHO_MAXIMO_ROTEIRO)
    if value.size > (limite * 1024 * 1024):
        raise forms.ValidationError(
            _('Arquivo muito grande. Tamanho não deve exceder {0} MB.'.format(limite)))


class RequisicaoForm(forms.ModelForm):
    roteiro = forms.FileField(allow_empty_file=False, validators=[
                              file_size], required=False)

    def clean(self):

        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fim = cleaned_data.get('hora_fim')
        if hora_inicio >= hora_fim:
            self.add_error(
                'hora_inicio', "O horário de início deve ser anterior a hora de encerramento!")

    def clean_data(self):
        data = self.cleaned_data['data']
        if data < datetime.date.today():
            raise forms.ValidationError("A data não pode estar no passado!")
        return data

    def clean_qt_alunos(self):
        qt_alunos = self.cleaned_data['qt_alunos']
        if qt_alunos < 1:
            raise forms.ValidationError(
                "A quantide de alunos deve ser maior que zero!")
        qt_maximo = self.cleaned_data['laboratorio'].capacidade_maxima
        if qt_alunos > qt_maximo:
            raise forms.ValidationError(
                "Capacidade do laboratório foi ultrapassada. Máximo permitido para o laboratório: %i alunos!" % qt_maximo)
        return qt_alunos


    class Meta:
        model = Requisicao
        fields = '__all__'
        exclude = ['itens', 'ocorrencias', 'status']
        widgets = {'itens_json': forms.HiddenInput(),
                   'escopo': forms.HiddenInput()}

    def __init__(self, escopo_id=0, usuario=None,  **kwargs):
        super(RequisicaoForm,self).__init__(**kwargs)
        if escopo_id:
            self.fields['laboratorio'].queryset = Laboratorio.objects.filter(status=SB.ATIVO, escopo__id=escopo_id)
        if usuario and not usuario.is_staff:
            self.fields['professor'].queryset =  Usuario.objects.filter(id=usuario.id)

class EditUserForm(forms.ModelForm):

    class Meta:
        model = Usuario
        fields = '__all__'
        exclude = ['password', 'date_joined', 'username']
        widgets = {'last_login': forms.DateTimeInput(attrs={'readonly': ''}),
                   'date_joined': forms.DateTimeInput(attrs={'readonly': ''}),
                   'username': forms.TextInput(attrs={'readonly': ''})}


class FormCancelamentoRequisicao(forms.Form):
    id = forms.IntegerField(required=False)
    id_confirmacao = forms.IntegerField(required=False)


class FormAdicionarObservacao(forms.Form):
    id = forms.IntegerField(required=False)
    observacao = forms.Textarea()


class FormFinalizacao(forms.Form):
    id = forms.IntegerField(required=False)
    ocorrencia = forms.Textarea()


class FormRejeicao(forms.Form):
    id = forms.IntegerField(required=False)
    ocorrencia = forms.Textarea()


class FormAprovacao(forms.Form):
    id = forms.IntegerField(required=False)
    itens_aprovados = forms.Textarea()
    observacao = forms.Textarea()


class FormDevolucao(forms.Form):
    id = forms.IntegerField(required=False)
    itens_devolvidos = forms.Textarea()
    observacao = forms.Textarea()


class FormSalvarCesta(forms.Form):
    nome = forms.TextInput()
    itens = forms.TextInput()
