from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from decouple import config

from .models import Requisicao, Usuario, Escopo

URL_SITE = config("URL_SITE", default='http://127.0.0.1:8000')
EMAIL_DEFAULT_SENDER = config(
    "EMAIL_DEFAULT_SENDER", default="no-reply@xxxx.com")


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 1200})
def enviar_email(subject=None, message=None, mstype=0, admins=False, id_escopo=0, recipients=[], object_id=None, statics=[], ** kwargs):

    subject = 'REQLAB - ' + subject
    adm_escopo = set(Escopo.objects.get(
        id=id_escopo).tecnicos.all() if id_escopo else [])
    if id_escopo and not adm_escopo:  # Se não tiver um responsável pelo escopo, deverá enviar para todos admins
        admins = True
    admins = set(Usuario.objects.filter(is_staff=True) if admins else [])
    recipients = set(Usuario.objects.filter(id__in=recipients))
    dest = set([user.email for user in recipients.union(
        admins).union(adm_escopo) if user.email]).union(set(statics))

    objeto = Requisicao.objects.get(
        id=object_id) if mstype == 1 else Usuario.objects.get(id=object_id)

    if mstype in (1, 2, 3) and len(dest):
        html_message = render_to_string('lab/includes/mail_template.html', {
            'objeto': objeto,
            'message': message,
            'tipo': mstype,
            'url_site': URL_SITE
        })
        plain_message = strip_tags(html_message)
        try:
            send_mail(subject=subject,
                      message=plain_message,
                      from_email=EMAIL_DEFAULT_SENDER,
                      recipient_list=list(dest),
                      html_message=html_message
                      )
        except Exception as erro:
            raise Exception("Erro ao enviar email: {0}".format(erro))
