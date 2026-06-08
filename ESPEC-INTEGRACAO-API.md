# Especificação — Integração com API de Projetos (Controle de Implantação Teknisa)

**Sistema consumidor:** Controle Implantação Retail BR
**Sistema origem:** Controle de Implantação Teknisa (`https://controle-implantacao-teknisa.vercel.app`)
**Tipo:** Cliente consumidor de API REST read-only
**Versão da spec:** 1.0
**Data:** 2026-06-08

---

## 1. Objetivo

Importar e manter sincronizados os projetos cadastrados no sistema externo da Teknisa
para dentro do Controle Implantação Retail BR, reaproveitando a estrutura de
`ERPProjetoDB` / `ERPModuloDB` já existente.

O nosso sistema atua **apenas como consumidor** (faz `GET`). Nenhum dado é enviado de volta.

### Decisões de design aprovadas

| Tema | Decisão |
|------|---------|
| **Disparo da sincronização** | **Ambos** — botão manual (admin) + cron automático |
| **Projeto já existente (mesmo UUID)** | **Revisão caso a caso** — fila de reconciliação onde o usuário decide por projeto |
| **Campos extras do cliente** | **Criar colunas novas** no `ERPProjetoDB` |

---

## 2. Arquitetura geral

```
┌──────────────────────────────┐         GET /api/projetos-export
│  Controle Implantação Teknisa │  ◄──────────────────────────────────┐
│  (API externa, read-only)     │      Authorization: Bearer <KEY>     │
└──────────────────────────────┘                                       │
                                                                        │
┌───────────────────────────────────────────────────────────────────┐ │
│  Controle Implantação Retail BR (nosso sistema)                     │ │
│                                                                     │ │
│   api_integracao.py ──► busca + mapeia + detecta mudanças ──────────┘ │
│        │                                                              │
│        ▼                                                              │
│   ProjetoSyncPendente (fila de revisão)                              │
│        │                                                              │
│        ├── novos  ──────► (cron) insere automático                   │
│        │                  (manual) aparece na tela de revisão        │
│        │                                                             │
│        └── alterados ───► sempre vão para a tela de revisão          │
│                           (usuário decide: atualizar / manter)       │
│        │                                                             │
│        ▼ ao aplicar                                                  │
│   ERPProjetoDB + ERPModuloDB                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mudanças no banco de dados

### 3.1. Novas colunas em `erp_projetos`

```sql
ALTER TABLE erp_projetos ADD COLUMN external_id          VARCHAR(64) UNIQUE;   -- UUID da API
ALTER TABLE erp_projetos ADD COLUMN origem               VARCHAR(20) DEFAULT 'manual'; -- 'manual' | 'api'
ALTER TABLE erp_projetos ADD COLUMN nome_cliente         VARCHAR(250);
ALTER TABLE erp_projetos ADD COLUMN razao_social         VARCHAR(250);
ALTER TABLE erp_projetos ADD COLUMN cnpj                 VARCHAR(20);
ALTER TABLE erp_projetos ADD COLUMN local_cliente        VARCHAR(120);  -- cidade/UF
ALTER TABLE erp_projetos ADD COLUMN numero_proposta      VARCHAR(50);
ALTER TABLE erp_projetos ADD COLUMN coordenador_cliente  VARCHAR(150);
ALTER TABLE erp_projetos ADD COLUMN sponsor              VARCHAR(150);
ALTER TABLE erp_projetos ADD COLUMN coordenador_origem   VARCHAR(150);  -- nome cru vindo da API (fallback)
ALTER TABLE erp_projetos ADD COLUMN sincronizado_em      TIMESTAMP;
ALTER TABLE erp_projetos ADD COLUMN payload_hash         VARCHAR(64);   -- detecta mudança rápida

CREATE INDEX ix_erp_projetos_external_id ON erp_projetos(external_id);
```

### 3.2. Módulos

Sem mudança de schema. A `quantidade` vinda da API é **ignorada** — importamos
apenas o **nome do módulo** exatamente como vem da origem (respeitando o nome).

### 3.2b. Nova coluna em `colaboradores` (match de coordenador por e-mail)

```sql
ALTER TABLE colaboradores ADD COLUMN email VARCHAR(150);
CREATE INDEX ix_colaboradores_email ON colaboradores(email);
```

Necessária porque o vínculo de coordenador passa a ser por **e-mail** (ver §5.1/§6.1).
Inclui também ajuste nas telas de cadastro/edição de colaborador para preencher o e-mail.

### 3.3. Nova tabela — fila de revisão

```sql
CREATE TABLE integracao_sync_pendente (
    id              SERIAL PRIMARY KEY,
    external_id     VARCHAR(64) NOT NULL,
    nome            VARCHAR(250),               -- para exibição
    tipo_mudanca    VARCHAR(20) NOT NULL,       -- 'novo' | 'alterado'
    payload         TEXT NOT NULL,              -- JSON completo vindo da API
    diff            TEXT,                       -- JSON {campo: [local, api]} (só p/ alterados)
    projeto_id      INTEGER REFERENCES erp_projetos(id),  -- existente (só p/ alterados)
    detectado_em    TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'pendente',  -- pendente | aplicado | ignorado
    resolvido_em    TIMESTAMP,
    resolvido_por   VARCHAR(80)
);
CREATE INDEX ix_sync_pendente_status ON integracao_sync_pendente(status);
```

### 3.4. Nova tabela — log de execuções (auditoria)

```sql
CREATE TABLE integracao_sync_log (
    id            SERIAL PRIMARY KEY,
    executado_em  TIMESTAMP DEFAULT NOW(),
    tipo          VARCHAR(20),    -- 'manual' | 'automatico'
    total_api     INTEGER,
    novos         INTEGER,
    alterados     INTEGER,
    inalterados   INTEGER,
    erros         INTEGER,
    mensagem      TEXT
);
```

> Também adicionar `'Demanda Avulsa'` à constante `PROJETO_MODELOS` no `app.py`,
> pois a API expõe esse tipo e o nosso sistema hoje só tem Tradicional/Rollout/Treinamento.

---

## 4. Configuração (sem expor segredos no código)

Reaproveitar a tabela `AppConfig` (já usada para a chave da Anthropic):

| Chave (`AppConfig.chave`) | Conteúdo |
|---------------------------|----------|
| `INTEGRACAO_API_KEY`      | Bearer token fornecido pelo admin externo (`tek_rafael_...`) |
| `INTEGRACAO_BASE_URL`     | `https://controle-implantacao-teknisa.vercel.app` |
| `INTEGRACAO_CRON_SECRET`  | Token interno que protege o endpoint de cron |
| `INTEGRACAO_ULTIMO_SYNC`  | ISO 8601 do último sync (para usar `criado_apos`) |

Tela admin para preencher/testar essas chaves (igual à `/admin/configuracoes`).

---

## 5. Mapeamento de campos (De → Para)

### 5.1. Projeto

| Campo API (origem) | Campo nosso (`ERPProjetoDB`) | Transformação |
|--------------------|------------------------------|---------------|
| `id`               | `external_id`                | chave de deduplicação |
| `nome`             | `nome_projeto`               | `.upper()` (regra já vigente) |
| `nome_cliente`     | `nome_cliente`               | direto |
| `razao_social`     | `razao_social`               | direto |
| `cnpj`             | `cnpj`                       | direto |
| `tipo`             | `modelo_projeto`             | ver §5.2 |
| `status`           | `status`                     | ver §5.3 |
| `local`            | `local_cliente`              | direto |
| `numero_proposta`  | `numero_proposta`            | direto |
| `coordenador_teknisa` | `responsavel_id` + `coordenador_origem` | vínculo definido pela **chamada por e-mail** (§6.1) — cada lote já vem atribuído ao colaborador consultado; `coordenador_origem` guarda o nome cru para auditoria |
| `coordenador_cliente` | `coordenador_cliente`     | direto |
| `sponsor`          | `sponsor`                    | direto |
| `criado`           | `data_aceite`                | usa se `data_aceite` estiver vazio |
| `cronograma_pct`   | `percentual_conclusao`       | `null` → `0` |
| `modulos[]`        | → `ERPModuloDB` (N linhas)   | ver §5.4 |
| —                  | `origem = 'api'`             | marcador fixo |
| —                  | `sincronizado_em = now()`    | timestamp do sync |

### 5.2. Tipo → Modelo

| API `tipo`       | Nosso `modelo_projeto` |
|------------------|------------------------|
| `Tradicional`    | `Tradicional`          |
| `Rollout`        | `Rollout`              |
| `Treinamento`    | `Treinamento`          |
| `Demanda Avulsa` | `Demanda Avulsa` (novo)|

### 5.3. Status

| API `status` | Nosso `status` |
|--------------|----------------|
| `ativo`      | `Em andamento` |
| `encerrado`  | `Finalizado`   |
| `suspenso`   | `Paralisado`   |

(A API não tem equivalente a "Cancelado" — só projetos cancelados localmente.)

### 5.4. Módulos

Cada item de `modulos[]` vira um registro em `ERPModuloDB`, usando **apenas o nome**:

| API           | `ERPModuloDB`              |
|---------------|---------------------------|
| `modulo`      | `modulo` (nome respeitado, como vem da origem) |
| `quantidade`  | **ignorado**              |
| —             | `status_modulo='Planejado'` (padrão) |

Na atualização, os módulos do projeto são **substituídos** pelos vindos da API
(delete + reinsert), já que a API é a fonte da verdade dos módulos.

---

## 6. Fluxo de sincronização

### 6.1. Etapa comum — buscar e classificar (vínculo por e-mail)

```
1. Lê INTEGRACAO_API_KEY e INTEGRACAO_BASE_URL do AppConfig
2. Carrega coordenadores ativos COM e-mail preenchido
3. Para cada coordenador (loop por e-mail):
     GET {BASE_URL}/api/projetos-export?coordenador={email}&criado_apos={ultimo_sync}
     Header: Authorization: Bearer {API_KEY}
   → todos os projetos retornados são atribuídos a ESSE colaborador
     (responsavel_id conhecido, sem adivinhar pelo nome)
4. Para cada projeto retornado:
   a. calcula payload_hash (sha256 do JSON normalizado)
   b. busca ERPProjetoDB por external_id
      - não existe          → classifica como NOVO
      - existe, hash igual   → INALTERADO (ignora)
      - existe, hash difere  → ALTERADO (calcula diff campo a campo)
5. Grava resultado na fila integracao_sync_pendente
6. Registra integracao_sync_log (inclui nº de chamadas feitas)
```

> **Por que loop por e-mail?** A API só devolve o *nome* do coordenador no corpo
> da resposta; o e-mail existe apenas como filtro. Consultando um e-mail por vez,
> o vínculo `responsavel_id` fica 100% confiável. Custo: N chamadas (1 por
> coordenador) — aceitável no cron diário e dentro do limite de 1x/hora.
> Coordenadores **sem e-mail** cadastrado são ignorados na sincronização.

### 6.2. Disparo MANUAL (botão admin)

```
POST /admin/integracao/sincronizar
  → executa Etapa comum (§6.1)
  → redireciona para /admin/integracao/revisao
```

Tela de revisão `/admin/integracao/revisao`:

- **Seção "Novos projetos"** — lista com checkbox (marcar quais importar)
- **Seção "Projetos alterados"** — para cada projeto, tabela de diff:

  | Campo | Valor atual (local) | Valor da API | Ação |
  |-------|---------------------|--------------|------|
  | status | Em andamento | Finalizado | (•) Atualizar ( ) Manter |
  | cronograma_pct | 40 | 75 | (•) Atualizar ( ) Manter |

  Botões rápidos por projeto: **Aceitar tudo** / **Manter tudo** / **Ignorar**.

- Botão final **"Aplicar selecionados"** →
  `POST /admin/integracao/revisao/aplicar`

### 6.3. Disparo AUTOMÁTICO (cron Vercel)

```
GET /api/cron/sincronizar-projetos?token={CRON_SECRET}
  → executa Etapa comum (§6.1)
  → NOVOS:     insere automaticamente (origem='api')
  → ALTERADOS: ficam status='pendente' na fila (NÃO aplica sozinho)
  → grava log
```

Como o usuário pediu "perguntar para cada um", o cron **nunca sobrescreve**
automaticamente um projeto existente — apenas enfileira para revisão manual.
Um **badge no menu** indica "N projetos aguardando revisão".

`vercel.json`:
```json
{
  "crons": [
    { "path": "/api/cron/sincronizar-projetos?token=SEU_SECRET", "schedule": "0 6 * * *" }
  ]
}
```
> Plano free do Vercel: cron roda **1x/dia** (06:00 UTC no exemplo), dentro do
> limite recomendado pela API (máx. 1x/hora).

### 6.4. Aplicação das decisões

```
POST /admin/integracao/revisao/aplicar
  Para cada item marcado:
    - NOVO aceito       → cria ERPProjetoDB + ERPModuloDB
    - ALTERADO aceito   → atualiza só os campos marcados "Atualizar"
                          (campos "Manter" preservam o valor local)
    - ignorado          → status='ignorado' (não volta a aparecer)
  Atualiza INTEGRACAO_ULTIMO_SYNC
```

**Preservação de edições locais:** campos não marcados pela API (ex.: `responsavel_id`
ajustado manualmente, `ponto_atencao`, `valor_mensalidades`, `descricao` editada)
nunca são tocados, a menos que o usuário escolha explicitamente atualizá-los.

---

## 7. Componentes a criar

### 7.1. Novo módulo `api_integracao.py`

```python
def buscar_projetos_api(criado_apos=None) -> list[dict]
def _payload_hash(projeto: dict) -> str
def mapear_status(api_status: str) -> str
def mapear_tipo(api_tipo: str) -> str
def resolver_coordenador(nome: str, colabs) -> tuple[int|None, str]
def classificar_projetos(projetos_api: list) -> dict  # {novos, alterados, inalterados}
def calcular_diff(local: ERPProjetoDB, api: dict) -> dict
def aplicar_novo(api: dict) -> ERPProjetoDB
def aplicar_alteracao(projeto: ERPProjetoDB, api: dict, campos: list[str])
```

### 7.2. Rotas em `app.py`

| Rota | Método | Permissão | Função |
|------|--------|-----------|--------|
| `/admin/integracao` | GET | gestor | Config (chave/URL) + status + último log |
| `/admin/integracao/config` | POST | gestor | Salva chaves no AppConfig |
| `/admin/integracao/testar` | POST | gestor | Testa conexão (1 request, mostra total) |
| `/admin/integracao/sincronizar` | POST | gestor | Dispara sync manual → fila |
| `/admin/integracao/revisao` | GET | gestor | Tela de reconciliação |
| `/admin/integracao/revisao/aplicar` | POST | gestor | Aplica decisões |
| `/api/cron/sincronizar-projetos` | GET | token | Endpoint do cron |

### 7.3. Templates

- `templates/admin/integracao.html` — configuração + painel de status
- `templates/admin/integracao_revisao.html` — tela de novos + diffs

### 7.4. Permissões (matriz)

Novas chaves em `PERMISSOES`:
- `gerenciar_integracao` (config + sincronizar + revisar) — padrão: gestor

---

## 8. Segurança

- **Chave da API externa** guardada no banco (`AppConfig`), nunca no código/git.
- **HTTPS** obrigatório (a API já exige).
- **Endpoint de cron** protegido por `CRON_SECRET` — request sem o token correto retorna 401.
- **Timeout** de 15s nas chamadas externas + tratamento de falha (não derruba o sistema).
- **Rate limit**: respeitar máx. 1 chamada/hora; cron diário já atende.
- Acesso às telas de integração restrito a **gestores**.

---

## 9. Tratamento de erros

| Situação | Comportamento |
|----------|---------------|
| API key inválida (401) | Flash "Token inválido — verifique em Configurações" |
| Timeout / API fora do ar | Flash "Sistema externo indisponível, tente mais tarde"; log registra erro |
| JSON inesperado | Pula o projeto problemático, conta em `erros`, segue os demais |
| Coordenador não encontrado | Importa com `responsavel_id=NULL` + nome cru em `coordenador_origem` (aparece laranja na revisão) |
| `cronograma_pct = null` | Salva `percentual_conclusao = 0` |
| UUID duplicado em corrida | `external_id UNIQUE` protege; trata `IntegrityError` |

---

## 10. Plano de implementação (fases)

| Fase | Entrega | Esforço |
|------|---------|---------|
| **1** | Migração de schema (colunas + 2 tabelas) no Supabase | pequeno |
| **2** | `api_integracao.py` (buscar, mapear, classificar, diff) | médio |
| **3** | Tela `/admin/integracao` (config + testar conexão) | pequeno |
| **4** | Sync manual + tela de revisão/diff + aplicar | médio/grande |
| **5** | Endpoint de cron + `vercel.json` + badge "aguardando revisão" | pequeno |
| **6** | Log de auditoria + testes de todas as rotas | pequeno |

Cada fase é testável e implantável de forma independente.

---

## 11. Decisões confirmadas

1. ✅ **Match de coordenador por e-mail** — adiciona coluna `email` em
   `colaboradores`; sincronização faz loop consultando a API por e-mail
   (vínculo confiável, sem adivinhar pelo nome). Coordenadores sem e-mail
   não entram no sync.
2. ✅ **`data_conclusao`** — mantém o valor local; a API não fornece.
3. ✅ **Frequência do cron** — 1x/dia (06:00 UTC ≈ 03:00 BRT).
4. ⏳ **Quantidade de empresas por módulo** — recomendação: guardar em
   `quantidade_empresas` e exibir como selinho ("ERP (3 empresas)").
   *Aguardando confirmação final.*
```
