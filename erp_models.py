# -*- coding: utf-8 -*-
from datetime import datetime, date
from typing import List, Optional


class Modulo:
    """Representa um módulo ERP dentro de um projeto"""

    def __init__(self, id: int, projeto_id: int, nome: str, status: str = 'Planejado',
                 data_inicio: Optional[date] = None, data_conclusao: Optional[date] = None,
                 percentual_conclusao: float = 0):
        self.id = id
        self.projeto_id = projeto_id
        self.nome = nome
        self.status = status  # 'Planejado', 'Em Progresso', 'Concluído', 'Atrasado'
        self.data_inicio = data_inicio
        self.data_conclusao = data_conclusao
        self.percentual_conclusao = percentual_conclusao

    def dias_restantes(self) -> int:
        """Retorna dias até a conclusão do módulo"""
        if self.data_conclusao is None:
            return 0
        delta = self.data_conclusao - date.today()
        return delta.days

    def esta_atrasado(self) -> bool:
        """Verifica se o módulo está atrasado"""
        if self.status == 'Concluído':
            return False
        return self.dias_restantes() < 0

    def __repr__(self):
        return f"Modulo(id={self.id}, nome='{self.nome}', status='{self.status}', {self.percentual_conclusao}%)"


class Unidade:
    """Representa uma unidade/loja envolvida em um projeto"""

    def __init__(self, id: int, projeto_id: int, nome: str, status: str = 'Não iniciado',
                 data_inicio: Optional[date] = None, data_conclusao: Optional[date] = None):
        self.id = id
        self.projeto_id = projeto_id
        self.nome = nome
        self.status = status  # 'Não iniciado', 'Em andamento', 'Finalizado', 'Atrasado'
        self.data_inicio = data_inicio
        self.data_conclusao = data_conclusao

    def dias_restantes(self) -> int:
        """Retorna dias até a conclusão da unidade"""
        if self.data_conclusao is None:
            return 0
        delta = self.data_conclusao - date.today()
        return delta.days

    def esta_atrasada(self) -> bool:
        """Verifica se a unidade está atrasada"""
        if self.status == 'Finalizado':
            return False
        return self.dias_restantes() < 0

    def __repr__(self):
        return f"Unidade(id={self.id}, nome='{self.nome}', status='{self.status}')"


class Atividade:
    """Representa uma atividade/nota de reunião de um projeto"""

    def __init__(self, id: int, projeto_id: int, titulo: str, data_reuniao: date,
                 descricao: str = '', responsavel_nota: str = '', status: str = 'Aberta',
                 concluida: bool = False):
        self.id = id
        self.projeto_id = projeto_id
        self.titulo = titulo
        self.descricao = descricao
        self.data_reuniao = data_reuniao if isinstance(data_reuniao, date) else datetime.strptime(str(data_reuniao), "%Y-%m-%d").date()
        self.responsavel_nota = responsavel_nota
        self.status_atividade = status  # 'Aberta', 'Em Progresso', 'Concluída'
        self.concluida = concluida

    def __repr__(self):
        return f"Atividade(id={self.id}, titulo='{self.titulo}', concluida={self.concluida})"


class Projeto:
    """Representa um projeto de implantação ERP"""

    def __init__(self, id: int, nome: str, data_aceite: date, data_conclusao: Optional[date] = None,
                 status: str = 'Em andamento', valor_mensalidades: float = 0,
                 responsavel: Optional[str] = None, descricao: str = '',
                 numero_unidades: int = 1, potencial_cliente: str = 'Médio',
                 tipo_projeto: str = 'Novo'):
        self.id = id
        self.nome = nome
        self.data_aceite = data_aceite if isinstance(data_aceite, date) else datetime.strptime(str(data_aceite), "%Y-%m-%d").date()
        if data_conclusao is None:
            self.data_conclusao = None
        else:
            self.data_conclusao = data_conclusao if isinstance(data_conclusao, date) else datetime.strptime(str(data_conclusao), "%Y-%m-%d").date()
        self.status = status  # 'Em andamento', 'Finalizado', 'Cancelado'
        self.valor_mensalidades = valor_mensalidades
        self.responsavel = responsavel
        self.descricao = descricao
        self.numero_unidades = numero_unidades
        self.potencial_cliente = potencial_cliente  # 'Pequeno', 'Médio', 'Grande', 'Estratégico'
        self.tipo_projeto = tipo_projeto  # 'Base', 'Novo'
        self.modulos: List[Modulo] = []
        self.unidades: List[Unidade] = []
        self.atividades: List[Atividade] = []

    def adicionar_modulo(self, modulo: Modulo):
        """Adiciona um módulo ao projeto"""
        self.modulos.append(modulo)

    def adicionar_unidade(self, unidade: Unidade):
        """Adiciona uma unidade ao projeto"""
        self.unidades.append(unidade)

    def adicionar_atividade(self, atividade: Atividade):
        """Adiciona uma atividade/nota ao projeto"""
        self.atividades.append(atividade)

    def dias_restantes(self) -> int:
        """Retorna dias até a conclusão do projeto. Retorna 0 se não há data definida."""
        if self.data_conclusao is None:
            return 0
        delta = self.data_conclusao - date.today()
        return delta.days

    def esta_atrasado(self) -> bool:
        """Verifica se o projeto está atrasado"""
        if self.status == 'Finalizado':
            return False
        if self.data_conclusao is None:
            return False
        return self.dias_restantes() < 0

    def percentual_geral(self) -> float:
        """Calcula percentual geral de conclusão do projeto"""
        if not self.modulos:
            return 0
        return sum(m.percentual_conclusao for m in self.modulos) / len(self.modulos)

    def modulos_em_progresso(self) -> List[Modulo]:
        """Retorna módulos em progresso"""
        return [m for m in self.modulos if m.status in ['Em Progresso', 'Planejado']]

    def modulos_atrasados(self) -> List[Modulo]:
        """Retorna módulos atrasados"""
        return [m for m in self.modulos if m.esta_atrasado()]

    def unidades_iniciadas(self) -> List[Unidade]:
        """Retorna unidades já iniciadas"""
        return [u for u in self.unidades if u.status in ['Em andamento', 'Finalizado']]

    def unidades_atrasadas(self) -> List[Unidade]:
        """Retorna unidades atrasadas"""
        return [u for u in self.unidades if u.esta_atrasada()]

    def valor_total_mes(self) -> float:
        """Retorna valor total do mês (para cálculos de receita)"""
        if self.status == 'Finalizado':
            return 0
        return self.valor_mensalidades

    def atividades_abertas(self) -> List[Atividade]:
        """Retorna atividades não concluídas"""
        return [a for a in self.atividades if not a.concluida]

    def __repr__(self):
        return f"Projeto(id={self.id}, nome='{self.nome}', tipo='{self.tipo_projeto}', potencial='{self.potencial_cliente}', {self.percentual_geral():.1f}%)"
