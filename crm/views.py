import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from .models import Cliente, Notificacao


REGRAS = {
    'ex_fiel': {
        'tipo':'push','desconto':15,
        'template':"Oi, {nome}! 😢 Sentimos sua falta no SuperDev! Que tal voltar hoje com 15% OFF em {categoria}? Seu produto favorito está esperando por você! 🛒",
        'oferta':"Cupom VOLTEI15 – 15% de desconto em {categoria}",
        'categoria_alvo':'Mercearia','nova_categoria':'Padaria',
        'sugestao':"Aproveite e conheça nossa Padaria Artesanal! Pão fresquinho todo dia 🍞",
    },
    'vegetariano_incompleto': {
        'tipo':'cupom','desconto':20,
        'template':"Olá, {nome}! 🥦 Você já tem ótimas escolhas no SuperDev. Mas sabia que nossos produtos de Limpeza Ecológica também são sustentáveis? Ganhe 20% OFF em Limpeza e Mercearia Básica hoje!",
        'oferta':"Cupom COMPLETO20 – 20% em Limpeza e Mercearia",
        'categoria_alvo':'Limpeza','nova_categoria':'Mercearia',
        'sugestao':"Complete sua cesta! Detergente biodegradável e grãos orgânicos com desconto 🌿",
    },
    'habitos_previsiveis': {
        'tipo':'push','desconto':10,
        'template':"Oi, {nome}! 🍼 Sua próxima reposição de fraldas e fórmula se aproxima! Já separamos tudo para você com 10% OFF. Adicione ao carrinho antes de acabar o estoque!",
        'oferta':"Cupom BEBE10 – 10% em Fraldas e Fórmula Infantil",
        'categoria_alvo':'Fraldas e Infantil','nova_categoria':'Hortifruti',
        'sugestao':"Que tal frutas e legumes frescos para a papinha do seu bebê? 🥕🍎",
    },
    'ativo': {
        'tipo':'email','desconto':5,
        'template':"Olá, {nome}! ⭐ Você é um dos nossos melhores clientes! Como agradecimento, preparamos 5% de desconto especial em toda a loja. Obrigado por escolher o SuperDev!",
        'oferta':"Cupom VIP5 – 5% em toda a loja",
        'categoria_alvo':'Geral','nova_categoria':'Feriados e Doces',
        'sugestao':"Conheça nossa seção de Feriados e Doces! Novidades toda semana 🎉",
    },
    'novo': {
        'tipo':'push','desconto':10,
        'template':"Olá, {nome}! 👋 Que bom ter você no SuperDev! Explore nossas seções e ganhe 10% OFF na sua próxima compra. Temos tudo que você precisa!",
        'oferta':"Cupom BEM10 – 10% na próxima compra",
        'categoria_alvo':'Geral','nova_categoria':'Mercearia',
        'sugestao':"Descubra nossa Mercearia Premium com produtos importados! 🌍",
    },
}

def gerar_mensagem(cliente):
    regra = REGRAS.get(cliente.perfil, REGRAS['novo'])
    msg   = regra['template'].format(nome=cliente.nome.split()[0], categoria=cliente.categoria_mais_comprada)
    oferta = regra['oferta'].format(categoria=cliente.categoria_mais_comprada)
    return msg, oferta, regra


def dashboard(request):
    clientes = Cliente.objects.all()
    total = clientes.count()
    por_perfil = {p['perfil']: p['total'] for p in clientes.values('perfil').annotate(total=Count('id'))}
    vermelhos = clientes.filter(status='vermelho').count()
    amarelos  = clientes.filter(status='amarelo').count()
    verdes    = clientes.filter(status='verde').count()
    stats = clientes.aggregate(ticket_medio=Avg('total_gasto_mes'), gasto_total=Sum('total_gasto_mes'), media_dias=Avg('dias_sem_comprar'))

    cats_qs = (
        clientes.values('categoria_mais_comprada')
        .annotate(total_clientes=Count('id'), gasto_total_cat=Sum('total_gasto_mes'), ticket_medio_cat=Avg('total_gasto_mes'))
        .order_by('-gasto_total_cat')
    )
    gasto_max = max((float(c['gasto_total_cat'] or 0) for c in cats_qs), default=1)
    categorias_rentaveis = [
        {**c, 'pct': float(c['gasto_total_cat'] or 0) / gasto_max * 100}
        for c in cats_qs
    ]

    notificacoes_recentes = Notificacao.objects.select_related('cliente').order_by('-criada_em')[:10]
    total_notif   = Notificacao.objects.count()
    notif_enviadas = Notificacao.objects.filter(status='enviada').count()

    ex_f = por_perfil.get('ex_fiel', 0)
    veg  = por_perfil.get('vegetariano_incompleto', 0)
    beb  = por_perfil.get('habitos_previsiveis', 0)
    ati  = por_perfil.get('ativo', 0)
    nov  = por_perfil.get('novo', 0)

    perfis_list = [
        ('ex_fiel',               'Ex-Fiéis',   '#ef4444', ex_f),
        ('vegetariano_incompleto','Cross-Sell',  '#f59e0b', veg),
        ('habitos_previsiveis',   'Perfil Bebê', '#22c55e', beb),
        ('ativo',                 'Ativos',      '#3b82f6', ati),
    ]

    perfis_sim = [
        {'key':'ex_fiel',               'label':'Ex-Fiel',     'icon':'🔴','qtd':ex_f,'bg':'rgba(239,68,68,0.07)','border':'rgba(239,68,68,0.3)','color':'#f87171','oferta':'15% OFF retorno'},
        {'key':'vegetariano_incompleto','label':'Cross-Sell',   'icon':'🟡','qtd':veg, 'bg':'rgba(245,158,11,0.07)','border':'rgba(245,158,11,0.3)','color':'#fbbf24','oferta':'20% OFF limpeza'},
        {'key':'habitos_previsiveis',   'label':'Perfil Bebê',  'icon':'🍼','qtd':beb, 'bg':'rgba(34,197,94,0.07)','border':'rgba(34,197,94,0.3)','color':'#4ade80','oferta':'10% OFF fraldas'},
        {'key':'ativo',                 'label':'Clientes VIP', 'icon':'⭐','qtd':ati, 'bg':'rgba(59,130,246,0.07)','border':'rgba(59,130,246,0.3)','color':'#60a5fa','oferta':'5% OFF toda loja'},
        {'key':'novo',                  'label':'Novos',        'icon':'👋','qtd':nov, 'bg':'rgba(99,102,241,0.07)','border':'rgba(99,102,241,0.3)','color':'#a5b4fc','oferta':'10% OFF boas-vindas'},
    ]

    context = {
        'top20_clientes': clientes.order_by('-total_gasto_mes')[:20],
        'total_clientes': total,
        'vermelhos': vermelhos, 'amarelos': amarelos, 'verdes': verdes,
        'ex_fieis': ex_f, 'vegetarianos': veg, 'bebes': beb, 'ativos': ati, 'novos': nov,
        'ticket_medio': stats['ticket_medio'] or 0,
        'gasto_total':  stats['gasto_total'] or 0,
        'media_dias':   stats['media_dias'] or 0,
        'categorias_rentaveis': categorias_rentaveis,
        'notificacoes_recentes': notificacoes_recentes,
        'total_notif': total_notif, 'notif_enviadas': notif_enviadas,
        'perfis_list': perfis_list,
        'perfis_sim':  perfis_sim,
        'status_json': json.dumps([vermelhos, amarelos, verdes]),
        'perfis_json': json.dumps([ex_f, veg, beb, ati, nov]),
        'cat_labels_json': json.dumps([c['categoria_mais_comprada'] for c in categorias_rentaveis]),
        'cat_gasto_json':  json.dumps([float(c['gasto_total_cat'] or 0) for c in categorias_rentaveis]),
    }
    return render(request, 'crm/dashboard.html', context)


def lista_clientes(request):
    perfil   = request.GET.get('perfil', '')
    status   = request.GET.get('status', '')
    busca    = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')

    clientes = Cliente.objects.all()
    if perfil:    clientes = clientes.filter(perfil=perfil)
    if status:    clientes = clientes.filter(status=status)
    if busca:     clientes = clientes.filter(nome__icontains=busca)
    if categoria: clientes = clientes.filter(categoria_mais_comprada=categoria)

    clientes = clientes.order_by('status', '-total_gasto_mes')

    todas_categorias = Cliente.objects.values_list('categoria_mais_comprada', flat=True).distinct().order_by('categoria_mais_comprada')

    context = {
        'clientes': clientes, 'total': clientes.count(),
        'perfil_selecionado': perfil, 'status_selecionado': status,
        'busca': busca, 'categoria_selecionada': categoria,
        'todas_categorias': todas_categorias,
    }
    return render(request, 'crm/lista_clientes.html', context)


def detalhe_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    notificacoes = cliente.notificacoes.order_by('-criada_em')
    msg_preview, oferta_preview, regra = gerar_mensagem(cliente)
    context = {
        'cliente': cliente, 'notificacoes': notificacoes,
        'msg_preview': msg_preview, 'oferta_preview': oferta_preview,
        'nova_categoria': regra['nova_categoria'],
        'sugestao': regra['sugestao'], 'desconto': regra['desconto'],
    }
    return render(request, 'crm/detalhe_cliente.html', context)


def notificacoes_view(request):
    notificacoes = Notificacao.objects.select_related('cliente').order_by('-criada_em')
    return render(request, 'crm/notificacoes.html', {'notificacoes': notificacoes})


# ── API ──────────────────────────────────────────────────────────────────────

@require_POST
def disparar_perfil(request):
    data = json.loads(request.body)
    perfil = data.get('perfil')
    if perfil not in REGRAS:
        return JsonResponse({'erro': 'Perfil inválido'}, status=400)
    notifs = []
    for c in Cliente.objects.filter(perfil=perfil):
        msg, oferta, regra = gerar_mensagem(c)
        n = Notificacao.objects.create(
            cliente=c, tipo=regra['tipo'], mensagem=msg, oferta=oferta,
            desconto=regra['desconto'], categoria_alvo=regra['categoria_alvo'],
            status='enviada', enviada_em=timezone.now(),
        )
        notifs.append({'id':n.id,'cliente':c.nome,'cpf':c.cpf,'mensagem':msg,'oferta':oferta,
                       'tipo':regra['tipo'],'desconto':regra['desconto'],
                       'nova_categoria':regra['nova_categoria'],'sugestao':regra['sugestao']})
    return JsonResponse({'sucesso': True, 'total_disparado': len(notifs), 'notificacoes': notifs})


@require_POST
def disparar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    msg, oferta, regra = gerar_mensagem(cliente)
    n = Notificacao.objects.create(
        cliente=cliente, tipo=regra['tipo'], mensagem=msg, oferta=oferta,
        desconto=regra['desconto'], categoria_alvo=regra['categoria_alvo'],
        status='enviada', enviada_em=timezone.now(),
    )
    return JsonResponse({'sucesso': True, 'notificacao': {
        'id':n.id,'cliente':cliente.nome,'mensagem':msg,'oferta':oferta,
        'tipo':regra['tipo'],'desconto':regra['desconto'],
        'nova_categoria':regra['nova_categoria'],'sugestao':regra['sugestao'],
    }})


@require_POST
def limpar_notificacoes(request):
    Notificacao.objects.all().delete()
    return JsonResponse({'sucesso': True})


# ── helper usado pelo dashboard para montar lista de perfis do simulador ──────
# (já incluído na view dashboard via context abaixo — este bloco é só documentação)
