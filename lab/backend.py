from social_core.backends.oauth import BaseOAuth2
from lab.models import Usuario
from lab.tasks import enviar_email


class SUAPBackendOauth2(BaseOAuth2):
    name = 'suap'
    AUTHORIZATION_URL = 'https://suap.ifba.edu.br/o/authorize/'
    ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://suap.ifba.edu.br/o/token/'
    ID_KEY = 'identificacao'
    RESPONSE_TYPE = 'code'
    REDIRECT_STATE = True
    STATE_PARAMETER = True
    USER_DATA_URL = 'https://suap.ifba.edu.br/api/eu/'

    def user_data(self, access_token, *args, **kwargs):
        return self.request(
            url=self.USER_DATA_URL,
            data={'scope': kwargs['response']['scope']},
            method='GET',
            headers={'Authorization': 'Bearer {0}'.format(access_token)}
        ).json()

    def get_user_details(self, response):
        splitted_name = response['nome'].split()
        first_name, last_name = splitted_name[0], ''
        if len(splitted_name) > 1:
            last_name = splitted_name[-1]

        user = {}
        user.setdefault('username', response[self.ID_KEY])
        user.setdefault('first_name', first_name.strip())
        user.setdefault('last_name', last_name.strip())
        user.setdefault('email', response['email'])

        user_local = self.get_user_local(user)

        return {
            'username': user_local.username,
            'first_name': user_local.first_name,
            'last_name': user_local.last_name,
            'email': user_local.email
        }

    def get_user_local(self, user: dict):
        try:
            user_local = Usuario.objects.get(username=user.get('username'))
        except Usuario.DoesNotExist:  # Primeiro acesso - Cria o usuário
            user_local.first_name = user.ger('first_name')
            user_local.username = user.get('username'),
            user_local.first_name = user.get('first_name'),
            user_local.last_name = user.get('last_name'),
            user_local.email = user.get('email')
            user_local.save()
            enviar_email.delay(subject="Novo usuário criado automaticamente",
                               message="O usuário abaixo foi criado de forma automática, através de login do SUAP",
                               mstype=3,
                               admins=True,
                               object_id=int(user_local.id)
                               )
        return user_local
