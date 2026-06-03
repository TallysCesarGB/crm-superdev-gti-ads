from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    CATEGORIA_CHOICES = [
        ('Mercearia', 'Mercearia'),
        ('Vegetariano e Saudavel', 'Vegetariano e Saudável'),
        ('Fraldas e Infantil', 'Fraldas e Infantil'),
        ('Hortifruti', 'Hortifruti'),
        ('Bebidas e Cervejas', 'Bebidas e Cervejas'),
        ('Limpeza', 'Limpeza'),
        ('Padaria', 'Padaria'),
        ('Acougue e Peixaria', 'Açougue e Peixaria'),
        ('Feriados e Doces', 'Feriados e Doces'),
        ('Limgue e Peixaria', 'Linguiça e Peixaria'),
    ]

    PERFIL_CHOICES = [
        ('ex_fiel', 'Ex-Fiel (Risco de Churn)'),
        ('vegetariano_incompleto', 'Vegetariano Incompleto (Cross-Sell)'),
        ('habitos_previsiveis', 'Hábitos Previsíveis (Bebê)'),
        ('ativo', 'Cliente Ativo'),
        ('novo', 'Cliente Novo'),
    ]

    STATUS_CHOICES = [
        ('vermelho', 'Vermelho - Alto Risco'),
        ('amarelo', 'Amarelo - Atenção'),
        ('verde', 'Verde - Saudável'),
    ]

    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=20, unique=True)
    dias_sem_comprar = models.IntegerField(default=0)
    total_gasto_mes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    categoria_mais_comprada = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    perfil = models.CharField(max_length=30, choices=PERFIL_CHOICES, default='ativo')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='verde')
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.cpf}"

    def classificar(self):
        if self.total_gasto_mes >= 600 and self.dias_sem_comprar >= 20:
            self.perfil = 'ex_fiel'
            self.status = 'vermelho'
        elif self.categoria_mais_comprada == 'Vegetariano e Saudavel':
            self.perfil = 'vegetariano_incompleto'
            self.status = 'amarelo'
        elif self.categoria_mais_comprada == 'Fraldas e Infantil':
            self.perfil = 'habitos_previsiveis'
            self.status = 'verde'
        elif self.dias_sem_comprar <= 7 and self.total_gasto_mes >= 400:
            self.perfil = 'ativo'
            self.status = 'verde'
        else:
            self.perfil = 'novo'
            self.status = 'amarelo' if self.dias_sem_comprar >= 15 else 'verde'
        return self


class Notificacao(models.Model):
    TIPO_CHOICES = [
        ('push', 'Notificação Push'),
        ('cupom', 'Cupom de Desconto'),
        ('email', 'E-mail Personalizado'),
        ('sms', 'SMS'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('enviada', 'Enviada'),
        ('lida', 'Lida'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notificacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='push')
    mensagem = models.TextField()
    oferta = models.CharField(max_length=200, blank=True)
    desconto = models.IntegerField(default=0)
    categoria_alvo = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    criada_em = models.DateTimeField(default=timezone.now)
    enviada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-criada_em']

    def __str__(self):
        return f"Notif [{self.tipo}] → {self.cliente.nome}"
