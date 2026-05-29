# Sistema de Controle de Férias

Um sistema local simples para gerenciar e controlar férias dos colaboradores da equipe, prevenindo acúmulo de dias e alertando sobre conflitos de ausência.

## Funcionalidades Principais

✅ **Gestão de Colaboradores**
- Adicionar e remover colaboradores
- Registrar data de admissão
- Organizar por departamento/time

✅ **Controle de Férias**
- Calcular saldo automático baseado em data de admissão
- Registrar férias planejadas (10, 20 ou 30 dias)
- Rastreamento de períodos realizados

✅ **Alertas Inteligentes**
- Aviso quando 2+ pessoas do mesmo time saem juntas
- Opção de aprovar conflitos manualmente
- Acompanhamento de saldos críticos

✅ **Visualização Simples**
- Dashboard com próximas férias
- Calendário de disponibilidade
- Relatório de saldos por colaborador

## Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## Instalação

### 1. Opção A: Executar o script (Windows)

Duplo clique em **run.bat** na pasta do projeto. O script:
- Instala as dependências automaticamente
- Inicia a aplicação

### 2. Opção B: Instalar manualmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar aplicação
python app.py
```

## Uso

### 1. Acessar a Aplicação

Após iniciar, acesse no navegador:
```
http://localhost:5000
```

### 2. Adicionar Colaborador

1. Clique em **"+ Colaborador"** no menu
2. Preencha:
   - Nome
   - Data de admissão
   - Departamento/Time
3. Clique "Salvar Colaborador"

**Obs:** Férias só podem ser tomadas após 12 meses da admissão.

### 3. Registrar Férias

1. Clique em **"+ Férias"** no menu
2. Selecione o colaborador
3. Escolha as datas de início e fim
4. O sistema calcula:
   - Número de dias
   - Saldo disponível
   - Conflitos com outros colaboradores

#### Se houver Conflito:
- Sistema exibe alerta mostrando quem mais sai de férias
- Opção de **"Aprovar Mesmo Assim"** se necessário
- Alerta desaparece do dashboard após aprovação

### 4. Visualizar Dashboard

A página principal mostra:
- **Conflitos Detectados**: Alertas de múltiplas ausências
- **Saldos Críticos**: Colaboradores com pouco saldo
- **Próximas Férias**: Períodos agendados nos próximos 90 dias
- **Saldos Atuais**: Visualização rápida do saldo de cada um

## Regras de Validação

⚠️ O sistema **não permite**:
- Férias antes de 12 meses de admissão
- Período já registrado 2 vezes (mesmo período duplicado)
- Saldo negativo (solicitar mais dias que tem disponível)
- Datas inválidas (fim antes de início)

## Estrutura de Dados

Todos os dados são armazenados em **ferias_data.xlsx** (Excel) na pasta `data/`:

- **Colaboradores**: Lista de colaboradores e datas de admissão
- **Férias Planejadas**: Períodos agendados e confirmados
- **Férias Realizadas**: Histórico de férias já usadas

## Cálculo de Saldo

```
Saldo = (Anos desde admissão) × 30 - Dias já utilizados

Exemplo:
- Admitido: 2022-06-15
- Hoje: 2026-06-25
- Direito: 4 anos × 30 = 120 dias
- Utilizados em 2025: 50 dias
- Saldo atual: 120 - 50 = 70 dias
```

## Parar a Aplicação

Pressione **Ctrl + C** no terminal onde a aplicação está rodando.

## Problemas Comuns

**"Module not found"**
- Execute `pip install -r requirements.txt` novamente

**Porta 5000 já está em uso**
- Mude a porta em `app.py`: `app.run(port=5001)`

**Arquivo Excel corrompido**
- Feche o arquivo `data/ferias_data.xlsx` se estiver aberto
- Delete-o para recriar vazio

## Suporte

Para dúvidas sobre o uso ou erros, verifique:
1. Se todas as dependências estão instaladas
2. Se o arquivo Excel não está aberto
3. Se as datas estão no formato correto (YYYY-MM-DD)
