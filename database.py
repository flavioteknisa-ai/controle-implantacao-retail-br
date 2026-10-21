# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id             = db.Column(db.Integer, primary_key=True)
    username       = db.Column(db.String(80), unique=True, nullable=False)
    nome           = db.Column(db.String(120), nullable=False)
    senha_hash     = db.Column(db.String(256), nullable=False)
    perfil         = db.Column(db.String(20), nullable=False, default='colaborador')
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True)
    ativo          = db.Column(db.Boolean, default=True)

    def set_senha(self, senha: str):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_gestor(self) -> bool:
        return self.perfil in ('gestor', 'master')

    @property
    def is_coordenador(self) -> bool:
        return self.perfil == 'coordenador'

    @property
    def can_manage(self) -> bool:
        """Gestor, Master ou Coordenador — acesso de gerenciamento"""
        return self.perfil in ('gestor', 'master', 'coordenador')


class ColaboradorDB(db.Model):
    __tablename__ = 'colaboradores'

    id                   = db.Column(db.Integer, primary_key=True)
    nome                 = db.Column(db.String(200), nullable=False)
    data_admissao        = db.Column(db.Date, nullable=False)
    time                 = db.Column(db.String(100), default='')
    cidade               = db.Column(db.String(100), default='')
    email                = db.Column(db.String(150), index=True)
    ativo                = db.Column(db.Boolean, default=True)
    saldo_ajuste         = db.Column(db.Integer, default=0)
    saldo_ajuste_motivo  = db.Column(db.Text)


class FeriasDB(db.Model):
    __tablename__ = 'ferias'

    id                 = db.Column(db.Integer, primary_key=True)
    colaborador_id     = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False, index=True)
    data_inicio        = db.Column(db.Date, nullable=False)
    data_fim           = db.Column(db.Date, nullable=False)
    dias               = db.Column(db.Integer)
    # status: Solicitado | Planejado | Confirmado | Realizado | Cancelado
    status             = db.Column(db.String(50), default='Planejado', index=True)
    conflito_detectado = db.Column(db.Boolean, default=False)
    conflito_aprovado  = db.Column(db.Boolean, default=False)


# ─────────────────────────────────────────────────────────────────
# TABELAS: Projetos ERP / Implantação Retail BR
# ─────────────────────────────────────────────────────────────────

class ERPProjetoDB(db.Model):
    __tablename__ = 'erp_projetos'

    id                  = db.Column(db.Integer, primary_key=True)
    nome_projeto        = db.Column(db.String(250), nullable=False, unique=True)
    data_aceite         = db.Column(db.Date, nullable=False)
    data_conclusao      = db.Column(db.Date, nullable=True)
    status              = db.Column(db.String(50), default='Em andamento', index=True)
    # Em andamento, Paralisado, Finalizado, Cancelado
    responsavel_id      = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True, index=True)
    valor_mensalidades  = db.Column(db.Float, default=0)
    descricao           = db.Column(db.Text)
    percentual_conclusao = db.Column(db.Float, default=0)
    numero_unidades     = db.Column(db.Integer, default=1)
    potencial_cliente   = db.Column(db.String(50), default='Médio')
    tipo_projeto        = db.Column(db.String(50), default='Novo')
    modelo_projeto      = db.Column(db.String(50), default='Tradicional')  # Tradicional | Rollout | Treinamento | Demanda Avulsa
    ponto_atencao       = db.Column(db.Boolean, default=False)
    comentarios_repasse = db.Column(db.Text)  # histórico de repasses entre coordenadores
    # ── Integração com API externa (Controle Implantação Teknisa) ──
    external_id         = db.Column(db.String(64), unique=True, index=True)  # UUID da API origem
    origem              = db.Column(db.String(20), default='manual')         # 'manual' | 'api'
    nome_cliente        = db.Column(db.String(250))
    razao_social        = db.Column(db.String(250))
    cnpj                = db.Column(db.String(20))
    local_cliente       = db.Column(db.String(120))                          # cidade/UF (legado; considerar usar cidade+estado)
    cidade              = db.Column(db.String(100))
    estado              = db.Column(db.String(2))
    numero_proposta     = db.Column(db.String(50))
    coordenador_cliente = db.Column(db.String(150))
    sponsor             = db.Column(db.String(150))
    coordenador_origem  = db.Column(db.String(150))                          # nome cru vindo da API
    sincronizado_em     = db.Column(db.DateTime)
    payload_hash        = db.Column(db.String(64))                           # detecta mudança
    criado_em           = db.Column(db.DateTime, default=datetime.now)
    atualizado_em       = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ERPModuloDB(db.Model):
    __tablename__ = 'erp_modulos_projeto'

    id                      = db.Column(db.Integer, primary_key=True)
    projeto_id              = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=False, index=True)
    modulo                  = db.Column(db.String(100), nullable=False)
    # Exemplos: RH, Financeiro, Estoque, Vendas, Compras, Produção, etc
    status_modulo           = db.Column(db.String(50), default='Planejado')
    # Planejado, Em Progresso, Concluído, Atrasado
    data_inicio_modulo      = db.Column(db.Date)
    data_conclusao_modulo   = db.Column(db.Date)
    percentual_conclusao    = db.Column(db.Float, default=0)
    criado_em               = db.Column(db.DateTime, default=datetime.now)


class ERPUnidadeDB(db.Model):
    __tablename__ = 'erp_unidades_projeto'

    id                      = db.Column(db.Integer, primary_key=True)
    projeto_id              = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=False, index=True)
    unidade                 = db.Column(db.String(150), nullable=False)
    # Nome da unidade/loja (ex: Matriz, Filial SP, Filial RJ)
    status_unidade          = db.Column(db.String(50), default='Não iniciado')
    # Não iniciado, Em andamento, Finalizado, Atrasado
    data_inicio_unidade     = db.Column(db.Date)
    data_conclusao_unidade  = db.Column(db.Date)
    criado_em               = db.Column(db.DateTime, default=datetime.now)


class ERPAtividadeDB(db.Model):
    __tablename__ = 'erp_atividades_projeto'

    id                  = db.Column(db.Integer, primary_key=True)
    projeto_id          = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=False, index=True)
    titulo              = db.Column(db.String(200), nullable=False)
    descricao           = db.Column(db.Text)
    data_reuniao        = db.Column(db.Date, nullable=False)
    responsavel_nota    = db.Column(db.String(200))
    responsavel_id      = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True, index=True)
    responsavel         = db.relationship('ColaboradorDB', foreign_keys=[responsavel_id], lazy='joined')
    status_atividade    = db.Column(db.String(50), default='Aberta')  # Aberta, Em Progresso, Concluída
    concluida           = db.Column(db.Boolean, default=False)
    criado_em           = db.Column(db.DateTime, default=datetime.now)
    atualizado_em       = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ERPRepasseDB(db.Model):
    __tablename__ = 'erp_repasses'

    id                          = db.Column(db.Integer, primary_key=True)
    projeto_id                  = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=False, index=True)
    data_repasse                = db.Column(db.Date, nullable=False)
    comentario                  = db.Column(db.Text, nullable=False)
    coordenador_temporario_id   = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True, index=True)
    cobertura_ate               = db.Column(db.Date)  # até quando a cobertura temporária vale
    criado_por                  = db.Column(db.String(120))
    criado_em                   = db.Column(db.DateTime, default=datetime.now)

    coordenador_temporario = db.relationship('ColaboradorDB', foreign_keys=[coordenador_temporario_id], lazy='joined')


# ─────────────────────────────────────────────────────────────────
# TABELA: Comissionamento Manual
# ─────────────────────────────────────────────────────────────────

class ComissionamentoDB(db.Model):
    __tablename__ = 'comissionamentos'

    id                      = db.Column(db.Integer, primary_key=True)
    consultor_id            = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True, index=True)
    consultor_nome          = db.Column(db.String(200))
    cliente                 = db.Column(db.String(200), nullable=False)
    data_comissao           = db.Column(db.Date, nullable=False, index=True)
    horas_comissionadas     = db.Column(db.Float, nullable=False)
    hora_fora_estado        = db.Column(db.String(10))  # HH:MM
    motivo                  = db.Column(db.Text)
    periodo_inicio          = db.Column(db.Date)  # Ex: 21/10
    periodo_fim             = db.Column(db.Date)  # Ex: 20/11
    criado_em               = db.Column(db.DateTime, default=datetime.now)
    atualizado_em           = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamento com colaborador (joined → evita N+1 nas listagens)
    consultor               = db.relationship('ColaboradorDB', backref='comissionamentos', lazy='joined')


# ─────────────────────────────────────────────────────────────────
# TABELA: Controle de Visitas
# ─────────────────────────────────────────────────────────────────

class VisitaDB(db.Model):
    __tablename__ = 'visitas'

    id               = db.Column(db.Integer, primary_key=True)
    regiao           = db.Column(db.String(100), nullable=False)          # RETAIL NN, RETAIL SS …
    colaborador_id   = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True, index=True)
    colaborador_nome = db.Column(db.String(200))                          # fallback quando sem vínculo
    status           = db.Column(db.String(50), default='PLANEJADA', index=True)  # PLANEJADA | CONCLUIDA | CANCELADA
    cliente          = db.Column(db.String(200), nullable=False)
    data_visita      = db.Column(db.Date, nullable=False, index=True)
    motivo           = db.Column(db.String(200))                          # STATUS REPORT | RELACIONAMENTO …
    contato          = db.Column(db.String(50))                           # Dono | Diretor | Supervisor
    cda              = db.Column(db.String(50))                           # PENDENTE | NÃO ENVIADO | ASSINADO …
    custo            = db.Column(db.String(50))                           # TEKNISA | CLIENTE | COMPARTILHADO
    endereco         = db.Column(db.Text)
    observacoes      = db.Column(db.Text)
    criado_em        = db.Column(db.DateTime, default=datetime.now)
    atualizado_em    = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    colaborador = db.relationship('ColaboradorDB', backref='visitas', foreign_keys=[colaborador_id], lazy='joined')


# ─────────────────────────────────────────────────────────────────
# TABELA: Configurações do Sistema (chave→valor)
# ─────────────────────────────────────────────────────────────────

class AppConfig(db.Model):
    __tablename__ = 'app_config'

    id         = db.Column(db.Integer, primary_key=True)
    chave      = db.Column(db.String(100), nullable=False, unique=True)
    valor      = db.Column(db.Text)
    atualizado = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def get(cls, chave: str, default: str = '') -> str:
        """Lê um valor de configuração do banco."""
        try:
            row = cls.query.filter_by(chave=chave).first()
            return row.valor if row and row.valor else default
        except Exception:
            return default

    @classmethod
    def set(cls, chave: str, valor: str):
        """Salva ou atualiza um valor de configuração."""
        row = cls.query.filter_by(chave=chave).first()
        if row:
            row.valor = valor
            row.atualizado = datetime.now()
        else:
            db.session.add(cls(chave=chave, valor=valor))
        db.session.commit()


# ─────────────────────────────────────────────────────────────────
# TABELA: Matriz de Permissões por Perfil
# ─────────────────────────────────────────────────────────────────

class PermissaoPerfil(db.Model):
    __tablename__ = 'permissoes_perfil'

    id      = db.Column(db.Integer, primary_key=True)
    perfil  = db.Column(db.String(20), nullable=False)   # colaborador | coordenador
    codigo  = db.Column(db.String(100), nullable=False)  # código da permissão

    __table_args__ = (
        db.UniqueConstraint('perfil', 'codigo', name='uq_permissao_perfil_codigo'),
    )


# ─────────────────────────────────────────────────────────────────
# TABELAS: Integração API de Projetos (Controle Implantação Teknisa)
# ─────────────────────────────────────────────────────────────────

class IntegracaoSyncPendente(db.Model):
    """Fila de revisão: projetos vindos da API aguardando decisão do usuário."""
    __tablename__ = 'integracao_sync_pendente'

    id            = db.Column(db.Integer, primary_key=True)
    external_id   = db.Column(db.String(64), nullable=False, index=True)
    nome          = db.Column(db.String(250))                # para exibição
    tipo_mudanca  = db.Column(db.String(20), nullable=False) # 'novo' | 'alterado'
    payload       = db.Column(db.Text, nullable=False)       # JSON completo da API
    diff          = db.Column(db.Text)                       # JSON {campo: [local, api]}
    projeto_id    = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=True)
    detectado_em  = db.Column(db.DateTime, default=datetime.now)
    status        = db.Column(db.String(20), default='pendente', index=True)  # pendente|aplicado|ignorado
    resolvido_em  = db.Column(db.DateTime)
    resolvido_por = db.Column(db.String(80))


class AgendaGestao(db.Model):
    """Agenda de Gestão — reuniões/visitas de acompanhamento com clientes."""
    __tablename__ = 'agenda_gestao'

    id                   = db.Column(db.Integer, primary_key=True)
    cliente              = db.Column(db.String(250), nullable=False)
    projeto_id           = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=True, index=True)
    data                 = db.Column(db.Date, nullable=False, index=True)
    consultor_id         = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True, index=True)
    responsavel_cliente  = db.Column(db.String(200))   # Nome do responsável no lado do cliente
    cargo_responsavel    = db.Column(db.String(150))   # Cargo/função desse responsável
    status               = db.Column(db.String(30), default='Prevista', index=True)  # Prevista | Executada | Cancelada
    apresentacao         = db.Column(db.String(30), default='Remoto')  # Remoto | Presencial
    observacoes          = db.Column(db.Text)
    criado_por_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    criado_em            = db.Column(db.DateTime, default=datetime.now)
    atualizado_em        = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    consultor  = db.relationship('ColaboradorDB', backref='agendas_gestao', foreign_keys=[consultor_id], lazy='joined')
    projeto    = db.relationship('ERPProjetoDB',  backref='agendas_gestao', foreign_keys=[projeto_id], lazy='joined')


class IntegracaoSyncLog(db.Model):
    """Log de auditoria de cada execução de sincronização."""
    __tablename__ = 'integracao_sync_log'

    id           = db.Column(db.Integer, primary_key=True)
    executado_em = db.Column(db.DateTime, default=datetime.now)
    tipo         = db.Column(db.String(20))   # 'manual' | 'automatico'
    total_api    = db.Column(db.Integer, default=0)
    novos        = db.Column(db.Integer, default=0)
    alterados    = db.Column(db.Integer, default=0)
    inalterados  = db.Column(db.Integer, default=0)
    erros        = db.Column(db.Integer, default=0)
    mensagem     = db.Column(db.Text)
