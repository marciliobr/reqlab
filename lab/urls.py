from datetime import datetime

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import forms, views

urlpatterns = [

    path('', views.home, name="home"),

    path('requisicao', views.form_requisicao, name="requisicao"),

    path('meus_dados', views.edit_user, name="edit_user"),

    path('cesta/', views.cesta, name="cesta"),

    path('cestas_salvas/<int:id>/', views.cestas_salvas, name='cestas_salvas'),

    path('lista_requisicoes', views.lista_requisicoes, name="lista_requisicoes"),

    path('gerir_requisicoes', views.gerir_requisicoes, name="gerir_requisicoes"),

    path('calendario', views.calendario, name="calendario"),

    path('calendario/<int:ano>/<int:mes>', views.calendario, name='calendario'),

    path('requisicao_detalhes/<int:id>/',
         views.requisicao_detalhes, name='requisicao_detalhes'),

    path('cesta_revisao/<int:id>/', views.cesta_revisao, name='cesta_revisao'),

    path('cesta_devolucao/<int:id>/',
         views.cesta_devolucao, name='cesta_devolucao'),

    path('registrar_cancelamento_requisicao', views.registrar_cancelamento_requisicao,
         name="registrar_cancelamento_requisicao"),

    path('adicionar_observacao', views.adicionar_observacao,
         name="adicionar_observacao"),

    path('finalizacao', views.finalizacao, name="finalizacao"),

    path('rejeicao', views.rejeicao, name="rejeicao"),

    path('requisicao_aprovar', views.requisicao_aprovar, name="requisicao_aprovar"),

    path('requisicao_devolver', views.requisicao_devolver,
         name="requisicao_devolver"),

    path('reports/reports_home', views.reports_home,
         name="reports_home"),

    path('reports/estoque_geral', views.report_estoque_geral,
         name="report_estoque_geral"),




    path('login/',
         LoginView.as_view
         (
             template_name='lab/includes/login.html',
             authentication_form=forms.LoginForm,

         ),
         name='login'),

    path('admin/login/',
         LoginView.as_view
         (
             template_name='lab/includes/login.html',
             authentication_form=forms.LoginForm,

         ),
         name='login'),


    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
