import base64
import json

from django.contrib.auth.backends import BaseBackend
from django.shortcuts import redirect

import requests

from .models import Usuario
from .tasks import enviar_email


class SUAPBackend(BaseBackend):

    url_base = 'https://suap.ifba.edu.br/api/v2/'
    timeout = 5.0

    def authenticate(self, request, username=None, password=None):
        self.username = username
        self.password = password

        url = self.url_base + 'autenticacao/token/'

        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        data = '{"username":"' + username + '", "password":"' + password + '"}'

        # Tentar obter o token, passando o usuário e a senha
        try:
            response = requests.post(
                url, headers=headers, data=data, timeout=self.timeout, verify=False)

        except Exception as erro:  # Erro de conexão
            print('Erro ao tentar acessar o SUAP {0}\n:'.format(str(erro)))
            return None

        # Verifica se o token está presente na resposta
        try:
            token = json.loads(response.content)['token']

            if len(token):
                self.token = token
            else:
                return None

        except IndexError or KeyError:
            return None

        except Exception as erro:
            print('Erro ao tentar acessar o SUAP {0}\n:'.format(str(erro)))
            return None

        try:
            usuario = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:  # Primeiro acesso - Cria o usuário
            usuario = self.get_user_SUAP(username, password, token)
            if usuario:
                usuario.save()
                if not usuario.is_active:
                    enviar_email.delay(subject="Usuário Pendente de Ativação",
                                       message="O usuário abaixo foi criado de forma automática, mas por segurança foi marcado como inativo.",
                                       mstype=3,
                                       admins=True,
                                       object_id=int(usuario.id)
                                       )
            else:
                print('Não foi possível criar o usuário{0}!'.format(username))
                return None

        # Atualizar password local
        if not usuario.check_password(password):
            usuario.set_password(password)
            usuario.save()

        return usuario

    def get_user_SUAP(self, username, password, token):
        autorizacao = str(base64.b64encode(
            (username + ":" + password).encode('utf-8'))).replace("b'", "")

        headers = {
            'Allow': 'GET, OPTIONS',
            'Accept': 'application/json',
            'Authorization': 'Basic ' + autorizacao,
            'X-CSRFToken': token
        }
        url = self.url_base + 'minhas-informacoes/meus-dados/'

        try:
            response = requests.get(
                url, headers=headers, timeout=self.timeout, verify=False)

        except Exception as erro:
            print('Erro ao tentar acessar o SUAP {0}\n:'.format(str(erro)))
            return None

        try:
            dados = json.loads(response.content)['vinculo']

        except Exception as erro:
            print('Erro ao obter dados do SUAP {0}\n:'.format(str(erro)))
            return None
        # TODO Alterar para configuração de campus permitidos

        usuario = Usuario.objects.create_user(
            username=self.username,
            email=dados.get('email', ''),
            first_name=dados.get('nome', self.username).split(maxsplit=1)[0],
            last_name=dados.get('nome', self.username).split(maxsplit=1)[-1],
            is_professor='PROF' in dados.get('cargo', ''),
            is_staff=False,
            is_active=('PROF' in dados.get('cargo', '')) and (
                dados.get('campus', '') == 'IRE'),
            password=password
        )

        return usuario

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except:
            return None

    def has_perm(self, user_obj, perm, obj=None):
        return False
