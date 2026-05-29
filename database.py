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

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(200), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    time          = db.Column(db.String(100), default='')
    cidade        = db.Column(db.String(100), default='')
    ativo         = db.Column(db.Boolean, default=True)


class FeriasDB(db.Model):
    __tablename__ = 'ferias'

    id                 = db.Column(db.Integer, primary_key=True)
    colaborador_id     = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    data_inicio        = db.Column(db.Date, nullable=False)
    data_fim           = db.Column(db.Date, nullable=False)
    dias               = db.Column(db.Integer)
    # status: Solicitado | Planejado | Confirmado | Realizado | Cancelado
    status             = db.Column(db.String(50), default='Planejado')
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
    status              = db.Column(db.String(50), default='Em andamento')
    # Em andamento, Finalizado, Cancelado
    responsavel_id      = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True)
    valor_mensalidades  = db.Column(db.Float, default=0)
    descricao           = db.Column(db.Text)
    percentual_conclusao = db.Column(db.Float, default=0)
    numero_unidades     = db.Column(db.Integer, default=1)
    potencial_cliente   = db.Column(db.String(50), default='Médio')
    tipo_projeto        = db.Column(db.String(50), default='Novo')
    ponto_atencao       = db.Column(db.Boolean, default=False)
    criado_em           = db.Column(db.DateTime, default=datetime.now)
    atualizado_em       = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ERPModuloDB(db.Model):
    __tablename__ = 'erp_modulos_projeto'

    id                      = db.Column(db.Integer, primary_key=True)
    projeto_id              = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=False)
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
    projeto_id              = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=False)
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
    projeto_id          = db.Column(db.Integer, db.ForeignKey('erp_projetos.id'), nullable=False)
    titulo              = db.Column(db.String(200), nullable=False)
    descricao           = db.Column(db.Text)
    data_reuniao        = db.Column(db.Date, nullable=False)
    responsavel_nota    = db.Column(db.String(200))
    status_atividade    = db.Column(db.String(50), default='Aberta')  # Aberta, Em Progresso, Concluída
    concluida           = db.Column(db.Boolean, default=False)
    criado_em           = db.Column(db.DateTime, default=datetime.now)
    atualizado_em       = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


# ─────────────────────────────────────────────────────────────────
# TABELA: Comissionamento Manual
# ─────────────────────────────────────────────────────────────────

class ComissionamentoDB(db.Model):
    __tablename__ = 'comissionamentos'

    id                      = db.Column(db.Integer, primary_key=True)
    consultor_id            = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    cliente                 = db.Column(db.String(200), nullable=False)
    data_comissao           = db.Column(db.Date, nullable=False)
    horas_comissionadas     = db.Column(db.Float, nullable=False)
    hora_fora_estado        = db.Column(db.String(10))  # HH:MM
    motivo                  = db.Column(db.Text)
    periodo_inicio          = db.Column(db.Date)  # Ex: 21/10
    periodo_fim             = db.Column(db.Date)  # Ex: 20/11
    criado_em               = db.Column(db.DateTime, default=datetime.now)
    atualizado_em           = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamento com colaborador
    consultor               = db.relationship('ColaboradorDB', backref='comissionamentos')


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
