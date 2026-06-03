from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/<int:pk>/', views.detalhe_cliente, name='detalhe_cliente'),
    path('notificacoes/', views.notificacoes_view, name='notificacoes'),
    # API
    path('api/disparar-perfil/', views.disparar_perfil, name='api_disparar_perfil'),
    path('api/disparar-cliente/<int:pk>/', views.disparar_cliente, name='api_disparar_cliente'),
    path('api/limpar-notificacoes/', views.limpar_notificacoes, name='api_limpar_notificacoes'),
]
