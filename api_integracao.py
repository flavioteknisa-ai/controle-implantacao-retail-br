# -*- coding: utf-8 -*-
"""
Cliente de integração com a API de Projetos do sistema Controle de Implantação Teknisa.

Somente leitura. Busca projetos por coordenador (via e-mail), mapeia para a
estrutura interna (ERPProjetoDB/ERPModuloDB), classifica novos/alterados e
aplica as decisões do usuário.

Veja a especificação completa em ESPEC-INTEGRACAO-API.md.
"""
import json
import hashlib
from datetime import datetime, date

from database import db, ERPProjetoDB, ERPModuloDB, ColaboradorDB


# ─── Exceções ────────────────────────────────────────────────────────────────

class ApiAuthError(Exception):
    """Token inválido / não autorizado (HTTP 401)."""


class ApiConfigError(Exception):
    """Configuração ausente (chave ou URL não preenchidas)."""


# ─── Mapeamentos de domínio ──────────────────────────────────────────────────

_STATUS_MAP = {
    'ativo':     'Em andamento',
    'encerrado': 'Finalizado',
    'suspenso':  'Paralisado',
}

_TIPO_MAP = {
    'Tradicional':    'Tradicional',
    'Rollout':        'Rollout',
    'Treinamento':    'Treinamento',
    'Demanda Avulsa': 'Demanda Avulsa',
}

# Campos do projeto controlados pela API (usados em diff e aplicação)
CAMPOS_SYNC = [
    'nome_projeto', 'status', 'modelo_projeto', 'percentual_conclusao',
    'nome_cliente', 'razao_social', 'cnpj', 'local_cliente',
    'numero_proposta', 'coordenador_cliente', 'sponsor',
    'responsavel_id', 'coordenador_origem',
]

# Rótulos amigáveis para a tela de revisão
ROTULOS_CAMPOS = {
    'nome_projeto':         'Nome do Projeto',
    'status':               'Status',
    'modelo_projeto':       'Modelo',
    'percentual_conclusao': '% Conclusão',
    'nome_cliente':         'Cliente',
    'razao_social':         'Razão Social',
    'cnpj':                 'CNPJ',
    'local_cliente':        'Local',
    'numero_proposta':      'Nº Proposta',
    'coordenador_cliente':  'Coord. Cliente',
    'sponsor':              'Sponsor',
    'responsavel_id':       'Responsável (Coordenador)',
    'coordenador_origem':   'Coord. (origem)',
    'modulos':              'Módulos',
}


def mapear_status(api_status):
    return _STATUS_MAP.get((api_status or '').lower(), 'Em andamento')


def mapear_tipo(api_tipo):
    return _TIPO_MAP.get((api_tipo or '').strip(), 'Tradicional')


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _payload_hash(api: dict) -> str:
    """SHA256 do payload da API (ignora chaves internas com prefixo '_')."""
    limpo = {k: v for k, v in api.items() if not k.startswith('_')}
    blob = json.dumps(limpo, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def _parse_criado(s):
    """ISO 8601 (com ou sem Z) → date. None se inválido."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00')).date()
    except Exception:
        try:
            return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
        except Exception:
            return None


def _norm(v):
    """Normaliza valores para comparação (None/''/espaços/decimais)."""
    if v is None:
        return ''
    if isinstance(v, float):
        # 45.0 e 45 devem ser iguais
        return str(int(v)) if v == int(v) else str(v)
    if isinstance(v, int):
        return str(v)
    return str(v).strip()


def _modulos_api(api: dict) -> list:
    """Lista de nomes de módulos vindos da API (quantidade ignorada)."""
    nomes = []
    for m in (api.get('modulos') or []):
        nome = (m.get('modulo') or '').strip()
        if nome:
            nomes.append(nome)
    return nomes


def mapear_campos(api: dict) -> dict:
    """Converte o payload da API para o dicionário de campos do ERPProjetoDB.
    O vínculo de responsável vem da atribuição por e-mail ('_colaborador_id')."""
    return {
        'nome_projeto':         (api.get('nome') or '').strip().upper(),
        'status':               mapear_status(api.get('status')),
        'modelo_projeto':       mapear_tipo(api.get('tipo')),
        'percentual_conclusao': float(api.get('cronograma_pct') or 0),
        'nome_cliente':         (api.get('nome_cliente') or '').strip() or None,
        'razao_social':         (api.get('razao_social') or '').strip() or None,
        'cnpj':                 (api.get('cnpj') or '').strip() or None,
        'local_cliente':        (api.get('local') or '').strip() or None,
        'numero_proposta':      (api.get('numero_proposta') or '').strip() or None,
        'coordenador_cliente':  (api.get('coordenador_cliente') or '').strip() or None,
        'sponsor':              (api.get('sponsor') or '').strip() or None,
        'responsavel_id':       api.get('_colaborador_id'),
        'coordenador_origem':   (api.get('coordenador_teknisa') or '').strip() or None,
    }


# ─── Busca na API (loop por e-mail de coordenador) ───────────────────────────

def buscar_projetos_api(api_key: str, base_url: str, criado_apos: str = None):
    """
    Consulta a API uma vez por coordenador ativo COM e-mail preenchido,
    filtrando por ?coordenador=<email>. Atribui cada projeto ao colaborador
    consultado (vínculo confiável).

    Retorna (projetos, erros, num_chamadas).
      - projetos: lista de dicts da API + '_colaborador_id' + '_colaborador_nome'
      - erros: lista de strings (uma por falha)
      - num_chamadas: total de requisições feitas
    Lança ApiConfigError / ApiAuthError.
    """
    import requests

    if not api_key or not base_url:
        raise ApiConfigError('Chave de API ou URL base não configuradas.')

    base = base_url.rstrip('/')
    headers = {'Authorization': f'Bearer {api_key}'}

    coords = (ColaboradorDB.query
              .filter(ColaboradorDB.ativo.is_(True))
              .filter(ColaboradorDB.email.isnot(None))
              .filter(ColaboradorDB.email != '')
              .order_by(ColaboradorDB.nome)
              .all())

    projetos = []
    erros = []
    chamadas = 0
    vistos = set()  # dedup por external_id

    for c in coords:
        params = {'coordenador': c.email}
        if criado_apos:
            params['criado_apos'] = criado_apos
        try:
            r = requests.get(f'{base}/api/projetos-export',
                             headers=headers, params=params, timeout=15)
            chamadas += 1
            if r.status_code == 401:
                raise ApiAuthError('Token inválido ou não autorizado (401).')
            if r.status_code != 200:
                erros.append(f'{c.nome} ({c.email}): HTTP {r.status_code}')
                continue
            data = r.json()
            for proj in data.get('projetos', []):
                ext = proj.get('id')
                if not ext or ext in vistos:
                    continue
                vistos.add(ext)
                proj['_colaborador_id']   = c.id
                proj['_colaborador_nome'] = c.nome
                projetos.append(proj)
        except ApiAuthError:
            raise  # aborta tudo: chave ruim
        except Exception as e:
            erros.append(f'{c.nome} ({c.email}): {e}')

    return projetos, erros, chamadas


# ─── Classificação (novo / alterado / inalterado) ────────────────────────────

def calcular_diff(projeto: ERPProjetoDB, api: dict) -> dict:
    """Retorna {campo: [valor_local_exibicao, valor_api_exibicao]} dos campos
    que mudaram. Apenas para exibição — a aplicação recalcula de mapear_campos()."""
    campos = mapear_campos(api)
    diff = {}

    # Mapa id->nome p/ exibir responsável de forma amigável
    def _nome_colab(cid):
        if not cid:
            return '—'
        c = ColaboradorDB.query.get(cid)
        return c.nome if c else f'ID {cid}'

    for campo in CAMPOS_SYNC:
        novo = campos.get(campo)
        atual = getattr(projeto, campo, None)
        if _norm(atual) == _norm(novo):
            continue
        if campo == 'responsavel_id':
            diff[campo] = [_nome_colab(atual), _nome_colab(novo)]
        else:
            diff[campo] = [_norm(atual) or '—', _norm(novo) or '—']

    # Módulos (compara conjunto de nomes)
    locais = sorted(m.modulo for m in
                    ERPModuloDB.query.filter_by(projeto_id=projeto.id).all())
    da_api = sorted(_modulos_api(api))
    if locais != da_api:
        diff['modulos'] = [', '.join(locais) or '—', ', '.join(da_api) or '—']

    return diff


def classificar_projetos(projetos_api: list) -> dict:
    """Classifica projetos da API em novos/alterados/inalterados.
    Retorna {'novos': [api...], 'alterados': [(projeto, api, diff)...],
             'inalterados': int}."""
    ext_ids = [p['id'] for p in projetos_api if p.get('id')]
    existentes = {}
    if ext_ids:
        for pr in ERPProjetoDB.query.filter(ERPProjetoDB.external_id.in_(ext_ids)).all():
            existentes[pr.external_id] = pr

    novos, alterados, inalterados = [], [], 0
    for api in projetos_api:
        ext = api.get('id')
        local = existentes.get(ext)
        if local is None:
            novos.append(api)
        else:
            if local.payload_hash == _payload_hash(api):
                inalterados += 1
            else:
                diff = calcular_diff(local, api)
                if diff:
                    alterados.append((local, api, diff))
                else:
                    inalterados += 1  # hash mudou mas campos relevantes iguais
    return {'novos': novos, 'alterados': alterados, 'inalterados': inalterados}


# ─── Aplicação ───────────────────────────────────────────────────────────────

def _sync_modulos(projeto_id: int, api: dict):
    """Substitui os módulos do projeto pelos vindos da API (delete + insert)."""
    ERPModuloDB.query.filter_by(projeto_id=projeto_id).delete()
    for nome in _modulos_api(api):
        db.session.add(ERPModuloDB(
            projeto_id=projeto_id,
            modulo=nome,
            status_modulo='Planejado',
            percentual_conclusao=0,
        ))


def aplicar_novo(api: dict) -> ERPProjetoDB:
    """Cria um novo ERPProjetoDB a partir do payload da API."""
    campos = mapear_campos(api)
    novo = ERPProjetoDB(
        external_id=api.get('id'),
        origem='api',
        data_aceite=_parse_criado(api.get('criado')) or date.today(),
        data_conclusao=None,
        valor_mensalidades=0,
        descricao='',
        numero_unidades=1,
        potencial_cliente='Médio',
        tipo_projeto='Novo',
        ponto_atencao=False,
        sincronizado_em=datetime.now(),
        payload_hash=_payload_hash(api),
        **campos,
    )
    db.session.add(novo)
    db.session.flush()  # garante novo.id
    _sync_modulos(novo.id, api)
    return novo


def aplicar_alteracao(projeto: ERPProjetoDB, api: dict, campos_aceitos: list):
    """Atualiza apenas os campos marcados pelo usuário. Campos não aceitos
    preservam o valor local. 'modulos' é tratado à parte."""
    campos = mapear_campos(api)
    for c in campos_aceitos:
        if c == 'modulos':
            _sync_modulos(projeto.id, api)
        elif c in campos:
            setattr(projeto, c, campos[c])
    # Marca como revisado nesta versão (evita re-prompt enquanto a API não mudar)
    projeto.payload_hash    = _payload_hash(api)
    projeto.sincronizado_em = datetime.now()
    projeto.origem          = 'api'
