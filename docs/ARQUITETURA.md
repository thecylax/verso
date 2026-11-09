# Arquitetura — Verso

Data: 4 de novembro de 2026.
Depende de [ESPECIFICACAO.md](ESPECIFICACAO.md). A ordem de construção está em [PLANO.md](PLANO.md).

## Como um agente deve usar este arquivo

1. Implemente o comportamento descrito em [ESPECIFICACAO.md](ESPECIFICACAO.md) com as estruturas deste arquivo.
2. Não troque biblioteca, rota, tabela, gramática de citação ou limite numérico por uma alternativa “equivalente”.
3. O catálogo de livros em JSON, mais abaixo, é a fonte única de abreviação, nome, quantidade de capítulos e aliases. O código do front e a validação do servidor nascem desse catálogo. Não use a fixture antiga da ABíbliaDigital que gravou Tito com 2 capítulos e Filemom com 4: aqueles números estão errados. Aqui Tito tem 3 e Filemom tem 1. A abreviação continua `tt` e `fm`.
4. Não grave no repositório o texto de nenhuma tradução bíblica. O texto capturado fica na linha da nota, no banco. Testes usam frases sintéticas.
5. O provedor externo é chamado somente dentro de `POST /api/documents`. Se estiver fora do ar nesse instante, a nota ainda é criada e a passagem guarda o erro. Abrir a nota não chama o provedor. Não substitua o provedor por outra API.

## Visão

```mermaid
flowchart LR
  subgraph client [PWA SvelteKit]
    Grid[Grade e pastas]
    Editor[Edicao e visualizacao]
    Stage[Apresentacao zoom gaveta]
    Parser[Topicos e citacoes]
  end
  subgraph api [FastAPI]
    Auth[Sessao]
    Notes[Pastas e notas]
    Bible[Captura na criacao]
    Cache[Cache de capitulos]
  end
  Db[(PostgreSQL)]
  Ext[Provedor compativel com ABibliaDigital]
  Grid --> Notes
  Editor --> Notes
  Stage --> Parser
  Notes --> Bible
  Auth --> Db
  Notes --> Db
  Bible --> Cache
  Cache --> Db
  Bible --> Ext
```

O navegador fala só com a origem do SvelteKit. O caminho `/api` é encaminhado ao FastAPI. O FastAPI chama o provedor bíblico apenas ao criar uma nota. A gaveta lê as passagens que voltaram gravadas nessa nota.

## Processos e portas

| Serviço Compose | Papel | Porta no host |
| --- | --- | --- |
| `postgres` | PostgreSQL 16 | 5432 |
| `api` | FastAPI via uvicorn | 8000 |
| `web` | Vite / SvelteKit em desenvolvimento | 5173 |

`web` depende de `api`. `api` depende de `postgres` saudável. O proxy do Vite encaminha `/api` para `http://api:8000` dentro da rede do Compose e para `http://127.0.0.1:8000` quando o front roda fora do Compose. O proxy precisa repassar `Set-Cookie`. Não configurar CORS e não colocar a API em outra origem do navegador: o cookie de sessão é da mesma origem da página.

## Variáveis de ambiente

Arquivo de exemplo na raiz: `.env.example`.

| Variável | Obrigatória | Valor de exemplo | Uso |
| --- | --- | --- | --- |
| `DATABASE_URL` | sim | `postgresql+psycopg://verso:verso@postgres:5432/verso` | SQLAlchemy |
| `COOKIE_SECURE` | sim | `false` em local, `true` atrás de HTTPS | flag `Secure` do cookie |
| `BIBLE_API_BASE_URL` | sim | `https://abibliadigital.api.br/api` | sem barra no fim |
| `BIBLE_API_TOKEN` | não | vazio | Bearer do provedor; vazio desliga a busca de texto |

Não há `SESSION_SECRET`. O valor do cookie já é um token aleatório de 32 bytes em `token_urlsafe`; o banco guarda só o SHA-256 hexadecimal.

## Provedor bíblico

Contrato de referência: OpenAPI 0.3.2 do projeto ABíbliaDigital, servidor de produção `https://abibliadigital.api.br/api` (o antigo `www.abibliadigital.com.br` responde 503). Material público do projeto: [repositório](https://github.com/omarciovsena/abibliadigital) e o site [abibliadigital.api.br](https://abibliadigital.api.br/).

Situação em 4 de novembro de 2026: o README desse repositório informa que o site e as APIs foram desativados em 1º de agosto de 2026. Uma checagem independente em 14 de outubro de 2026 não obteve resposta do host. A landing page pode continuar no ar sem a API. Por isso:

- o código chama apenas `BIBLE_API_BASE_URL`;
- o token, quando existir, vai no header `Authorization: Bearer <token>`;
- falha de rede, HTTP diferente de 200, corpo inesperado ou token vazio não impedem a criação da nota; a passagem afetada fica sem texto e com `error`;
- o agente não escolhe outra Bíblia, não faz scrape e não versiona o texto das traduções no repositório.

Não existe chamada a `GET /versions`. O seletor da conta oferece só estes slugs, nesta ordem: `nvi`, `acf`, `aa`, `ntlh`, `nvt`, `kjv`. A forma `[[slug:...]]` pode usar outro slug que caiba em `^[a-z0-9]{2,20}$`. Slug desconhecido pelo provedor vira erro na passagem, e a nota ainda é criada.

Chamada usada para o texto:

```http
GET {BIBLE_API_BASE_URL}/verses/{version}/{abbrev}/{chapter}
Accept: application/json
Authorization: Bearer {BIBLE_API_TOKEN}
```

O capítulo inteiro volta numa resposta. O campo `verses` é uma lista de objetos com `number` e `text`. O campo `chapter` pode ser objeto (`number`, `verses`) nesse endpoint. Guardar no cache só a lista `{ "number": number, "text": string }`, ordenada por `number`.

Timeout de 8 segundos. Uma nova tentativa só em erro de conexão. Não repetir em HTTP 4xx. Resposta 409 do provedor significa limite de taxa: não gravar cache. Essa chamada ocorre em três momentos: na criação da nota (todas as citações), no `PATCH` que muda `content_md` (só citações sem passagem gravada) e em `POST /api/documents/{id}/passages/refresh`, que o front chama ao abrir a nota quando há passagem pendente (refaz as que falharam por `upstream_unavailable`, `rate_limited` ou `bible_not_configured`).

O token é opcional: sem ele as requisições saem sem `Authorization` e o provedor aplica o limite anônimo. Só sem `BIBLE_API_BASE_URL` a passagem recebe `bible_not_configured` e `verses` vazio. Não há rota pública de versículos.

`refresh` devolve `{ "document": ..., "refresh": { "updated": n, "failed": m } }`: `updated` conta passagens pendentes que passaram a ter texto; `failed`, as que continuam pendentes. `document_out` traz `passages_pending` (há passagem com erro temporário).

## Modelo de dados

Identificadores UUID v4. Instantes `timestamptz` em UTC. Nomes de tabela no plural.

### `users`

| Coluna | Tipo | Regra |
| --- | --- | --- |
| `id` | uuid | pk |
| `name` | varchar(80) | obrigatório, já sem espaços nas pontas |
| `email` | varchar(254) | único, guardado em minúsculas |
| `password_hash` | text | Argon2id |
| `bible_version` | varchar(20) | padrão `nvi`, casa com `^[a-z0-9]{2,20}$` |
| `created_at` | timestamptz | default now |

### `sessions`

| Coluna | Tipo | Regra |
| --- | --- | --- |
| `id` | uuid | pk |
| `user_id` | uuid | fk `users.id` on delete cascade |
| `token_hash` | char(64) | único, SHA-256 hex do valor do cookie |
| `expires_at` | timestamptz | criação + 30 dias |
| `created_at` | timestamptz | default now |

### `folders`

| Coluna | Tipo | Regra |
| --- | --- | --- |
| `id` | uuid | pk |
| `user_id` | uuid | fk cascade, indexado junto de `parent_id` |
| `parent_id` | uuid nulo | fk `folders.id`; nulo é a raiz |
| `name` | varchar(80) | obrigatório, já sem espaços nas pontas |
| `created_at` | timestamptz | default now |

Índice único de irmãos: `(user_id, coalesce(parent_id, '00000000-0000-0000-0000-000000000000'), lower(name))`.

Profundidade máxima 20, contando a pasta nova. É proibido `parent_id` apontando para a própria pasta ou para um descendente. Apagar só quando não houver pasta filha nem nota dentro.

### `documents`

| Coluna | Tipo | Regra |
| --- | --- | --- |
| `id` | uuid | pk |
| `user_id` | uuid | fk cascade |
| `folder_id` | uuid nulo | fk `folders.id`; nulo é a raiz |
| `title` | varchar(160) | obrigatório depois da regra de título vazio |
| `content_md` | text | obrigatório, pode ser string vazia, máximo 200_000 caracteres |
| `passages` | jsonb | lista de passagens embutidas, nunca nulo; recalculada quando `content_md` muda, reaproveitando as já capturadas |
| `created_at` | timestamptz | default now, não muda em update |
| `updated_at` | timestamptz | muda a cada gravação de título ou corpo |

Índice `(user_id, folder_id, created_at desc)`.

Não há coluna nem rota para mover nota ou pasta de lugar nesta versão. `PATCH` da nota aceita `title` e `content_md`. `PATCH` da pasta aceita `name`. `passages` é escrito no `INSERT`, no `PATCH` que muda `content_md` e no `refresh`.

### `bible_chapter_cache`

| Coluna | Tipo | Regra |
| --- | --- | --- |
| `version` | varchar(20) | parte da pk |
| `abbrev` | varchar(8) | parte da pk |
| `chapter` | int | parte da pk |
| `verses` | jsonb | lista de `{number, text}` |
| `fetched_at` | timestamptz | momento da gravação |

A pk é `(version, abbrev, chapter)`. Não expira sozinha. Só grava corpo HTTP 200 com lista `verses` não vazia. O cache existe para a criação: capítulos repetidos na mesma nota, ou numa nota criada depois, não geram outra ida ao provedor. `GET` e `PATCH` de nota não leem o cache.

Toda leitura de pasta e de nota filtra `user_id` pela sessão. Id de outra pessoa produz o mesmo 404 de um id inexistente.

## HTTP

Prefixo `/api`. Corpo JSON. Erro único:

```json
{ "error": { "code": "not_found", "message": "Nota não encontrada." } }
```

| HTTP | `code` | Quando |
| --- | --- | --- |
| 401 | `unauthorized` | sem sessão, ou senha/e-mail de entrada inválidos |
| 404 | `not_found` | id ausente ou de outra pessoa |
| 409 | `conflict` | e-mail já cadastrado, ou pasta não vazia, ou nome de pasta repetido entre irmãos |
| 422 | `validation_error` | corpo inválido; `message` em português, o primeiro problema |

Mensagem de login inválido, sempre esta: "E-mail ou senha incorretos."

Cookie de sessão:

| Atributo | Valor |
| --- | --- |
| Nome | `session` |
| HttpOnly | sim |
| SameSite | `Lax` |
| Path | `/` |
| Secure | valor de `COOKIE_SECURE` |
| Max-Age | 30 dias |
| Valor | token cru; o banco guarda o hash |

Sessão vencida é tratada como ausência de sessão e o cookie é limpo.

Se o e-mail do login não existir, ainda assim rode a verificação Argon2 contra um hash fictício criado na subida do processo, para o tempo da resposta não denunciar a conta.

### `GET /api/health`

Sem sessão. `200` e `{ "status": "ok" }`.

### `POST /api/auth/register`

```json
{ "name": "Ana", "email": "ana@igreja.org", "password": "uma-senha" }
```

`201`:

```json
{ "id": "uuid", "name": "Ana", "email": "ana@igreja.org", "bible_version": "nvi" }
```

Define o cookie. E-mail é trimado e posto em minúsculas. Nome trimado, 1 a 80 caracteres. Senha com 8 a 128 caracteres.

### `POST /api/auth/login`

```json
{ "email": "ana@igreja.org", "password": "uma-senha" }
```

`200` com o mesmo objeto de pessoa. Define o cookie.

### `POST /api/auth/logout`

Exige sessão. Apaga a linha da sessão e limpa o cookie. `204` sem corpo.

### `GET /api/auth/me`

Exige sessão. `200` com o objeto de pessoa.

### `PATCH /api/auth/me`

```json
{ "bible_version": "acf" }
```

Exige sessão. Atualiza só a versão. `200` com o objeto de pessoa.

### Pastas

`GET /api/folders?parent_id=<uuid>`

Sem `parent_id`, lista a raiz da pessoa. Com `parent_id` de outra pessoa ou inexistente: `404`. Ordem: `lower(name)` crescente.

`200`:

```json
{
  "folders": [
    { "id": "uuid", "name": "Células", "parent_id": null, "created_at": "2026-11-04T12:00:00Z" }
  ],
  "breadcrumb": [
    { "id": "uuid", "name": "Células" }
  ]
}
```

Na raiz, `breadcrumb` é `[]`. Dentro de uma pasta, a trilha vai da raiz até a pasta atual, inclusive.

`POST /api/folders`

```json
{ "name": "Células", "parent_id": null }
```

`201` com o objeto da pasta. `parent_id` omitido ou `null` cria na raiz.

`PATCH /api/folders/{id}`

```json
{ "name": "Células de quarta" }
```

`200` com a pasta.

`DELETE /api/folders/{id}`

`204` se estiver vazia. `409` com mensagem "Esvazie a pasta antes de apagá-la." se houver filha ou nota.

### Notas

`GET /api/documents?folder_id=<uuid>`

Sem `folder_id`, lista a raiz. Não devolve `content_md`. Ordem: `created_at` decrescente.

```json
{
  "documents": [
    {
      "id": "uuid",
      "title": "A fé que permanece",
      "folder_id": null,
      "created_at": "2026-11-04T12:00:00Z",
      "updated_at": "2026-11-04T12:00:00Z"
    }
  ]
}
```

`POST /api/documents`

```json
{
  "folder_id": null,
  "title": "",
  "content_md": "# Graça\n\nJoão 3:16"
}
```

Este é o único endpoint que consulta o provedor bíblico. O servidor:

1. Faz o parse das citações de `content_md` com a gramática normativa deste arquivo, a mesma de `citations.ts`, implementada em `services/citations.py`. Citações naturais usam `bible_version` da conta. A forma explícita usa a versão escrita nela.
2. Resolve no máximo 40 citações, na ordem do texto, sem duplicata. Da 41ª em diante, a passagem entra com `error` `too_many` e `verses` vazio, sem chamada externa.
3. Para cada capítulo distinto ainda fora do cache, busca o capítulo uma vez, grava o cache e recorta.
4. Grava a lista em `passages` e devolve a nota. Falha de uma passagem não falha o `POST`.

`title` segue a regra de título vazio. `folder_id` omitido ou `null` cria na raiz. `content_md` omitido equivale a "". `201` com o documento completo, inclusive `content_md` e `passages`.

Forma de cada item de `passages`:

```json
{
  "version": "nvi",
  "abbrev": "jo",
  "chapter": 3,
  "start": 16,
  "end": 18,
  "book_name": "João",
  "verses": [{ "number": 16, "text": "..." }],
  "error": null
}
```

`book_name` sai do catálogo deste arquivo, não do provedor. `error` é `null`, `invalid_reference`, `not_found`, `upstream_unavailable`, `rate_limited`, `bible_not_configured` ou `too_many`. Referência inválida não chama o provedor: `invalid_reference`, `verses` vazio e `book_name` vazio se a abreviação for desconhecida. Capítulo inteiro usa `start` e `end` nulos. Se os dois números existirem e `end < start`, grave-os já trocados. Recorte vazio com capítulo válido grava `not_found`.

`GET /api/documents/{id}`

`200` com o documento completo, inclusive `passages`. Não chama o provedor.

`PATCH /api/documents/{id}`

```json
{ "title": "", "content_md": "# Graça\n\nJoão 3:16" }
```

Os dois campos são opcionais; pelo menos um precisa vir. Não envia nem altera `passages`. Não chama o provedor. Título efetivo, aplicado no servidor:

1. Se `title` vier e, depois do trim, tiver de 1 a 160 caracteres, esse é o título.
2. Se `title` vier vazio ou só com espaços, o título vira o texto do primeiro heading ATX do `content_md` resultante (o corpo novo, ou o corpo já salvo se o corpo não veio no PATCH), trimado e cortado em 160 caracteres.
3. Se ainda assim ficar vazio, o título é "Sem título".

Heading ATX é linha que começa com 1 a 6 `#`, um espaço e o resto do texto. Ignorar headings dentro de cerca de código.

`200` com o documento completo.

`DELETE /api/documents/{id}`

`204`.

### Recorte do capítulo

Usado só dentro do `POST /api/documents`. `start` nulo devolve o capítulo inteiro, na ordem de `number`. Só `start` presente equivale a `end = start`. Os dois números presentes formam um intervalo inclusivo; a troca quando `end < start` já ocorreu antes de gravar.

```python
def slice_verses(verses: list[dict], start: int | None, end: int | None) -> list[dict]:
    ordered = sorted(verses, key=lambda verse: verse["number"])
    if start is None:
        return ordered
    if end is None:
        end = start
    if end < start:
        start, end = end, start
    return [verse for verse in ordered if start <= verse["number"] <= end]
```

## Interface

Rotas SvelteKit:

| Rota | Tela |
| --- | --- |
| `/` | Entrar e criar conta |
| `/app` | Grade da raiz |
| `/app/pastas/[id]` | Grade da pasta |
| `/app/notas/nova` | Rascunho local até “Criar nota” |
| `/app/notas/[id]` | Nota já criada: edição, visualização, apresentação |

Layout de `/app` exige `GET /api/auth/me`. `401` manda para `/`. Pessoa já autenticada que abre `/` vai para `/app`.

### Tela de entrada

Cartão central com o tratamento de vidro. Estado "entrar": e-mail, senha, botão "Entrar", ação textual "Criar conta". Estado "criar": nome, e-mail, senha, botão "Criar conta", ação textual "Já tenho conta". Erro inline, vindo de `error.message`.

### Grade

Trilha de ancestrais no topo; na raiz, só o rótulo "Verso". Ações "Nova pasta", "Nova nota" e "Sair". Seletor "Versão bíblica" com os slugs fixos `nvi`, `acf`, `aa`, `ntlh`, `nvt` e `kjv`. A mudança grava `PATCH /api/auth/me` e vale para a próxima criação. Não há chamada ao provedor.

Pastas primeiro, notas depois. Cartão de pasta mostra o nome. Cartão de nota mostra o título e `created_at` com `Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })`.

Colunas da grade: 1 abaixo de 640px, 2 de 640px a 1023px, 3 a partir de 1024px.

"Nova pasta" pede o nome (prompt ou campo inline; um dos dois, sem biblioteca de modal extra) e faz `POST`. "Nova nota" navega para `/app/notas/nova?pasta=` com o id da pasta atual, ou sem query na raiz. O rascunho fica em `localStorage` na chave `verso.draft:{folderId}`, usando `root` na raiz. Fechar o navegador não apaga o rascunho. "Criar nota" faz o `POST`, apaga essa chave e substitui a URL por `/app/notas/{id}`.

Estado vazio: "Nada por aqui ainda." mais as duas ações de criar.

### Nota

Topo da nota já criada: campo de título, indicador "Salvando…" / "Salvo" / "Erro ao salvar", alternância "Editar" e "Ver", botão "Apresentar", botão "Apagar". No rascunho, o botão principal é "Criar nota"; não há "Apresentar" nem "Apagar" enquanto não existir id. Apagar pede confirmação nativa e, em sucesso, volta para `/app` ou `/app/pastas/{folder_id}`.

Edição: CodeMirror 6 com `@codemirror/lang-markdown` e tema escuro `@codemirror/theme-one-dark`. O campo de título fica fora do CodeMirror.

Visualização e apresentação: `markdown-it` com `html: false`, `linkify: true`, `breaks: false`. O HTML resultante entra em `{@html}` só porque o `html: false` escapa HTML cru da nota. Não ligar HTML cru.

Gravação da nota já criada: 800 ms depois da última mudança de título ou corpo, `PATCH` com os dois campos. `passages` não entra no corpo. Enquanto a pessoa digita durante o request, uma gravação nova espera a anterior terminar e então envia o estado mais recente. Falha mostra "Erro ao salvar" até a próxima tentativa ter sucesso. O rascunho só escreve em `localStorage`.

### Tópicos

Função pura `splitTopics(markdown: string): Topic[]`.

```ts
type Topic = {
  index: number;
  title: string;
  markdown: string;
  level: number; // 0 no preâmbulo; 1 a 6 nos headings
};
```

Algoritmo sobre o Markdown cru, não sobre o HTML:

1. Mascarar cercas que começam com ``` ou ~~~, até a cerca de fechamento, para que `#` lá dentro não vire heading.
2. Percorrer as linhas. Heading ATX: 0 a 3 espaços, 1 a 6 `#`, um espaço, texto até o fim da linha. Cortar um sufixo de `#` separado por espaço, se existir.
3. Cada heading abre um tópico cujo `markdown` inclui a linha do heading e as linhas seguintes até a linha anterior ao próximo heading.
4. Linhas antes do primeiro heading formam o tópico 0, título "Início", `level` 0. Se essas linhas forem só espaço, o tópico "Início" ainda existe e fica vazio.
5. Documento sem heading: um tópico "Início" com o texto todo.
6. `title` do heading é o texto do heading, já sem os `#`.

Na renderização, cada tópico é um `<section data-topic-index="{index}" id="topico-{index}">`. O heading do tópico, se houver, fica dentro da section.

Tópico ativo na visualização: `IntersectionObserver` no scroller da leitura, `rootMargin: "0px 0px -60% 0px"`. Entre as sections que cruzam a faixa de cima, vale a de menor `index` visível nessa faixa. Se nenhuma cruzar, manter o índice anterior. Começa em 0.

### Apresentação

Estado local da página da nota, não uma rota nova. Entrar força a visualização renderizada. Sair volta à visualização, mesmo que a pessoa estivesse editando antes.

```mermaid
stateDiagram-v2
  [*] --> Fora
  Fora --> Correndo: Apresentar
  Correndo --> Pausado: toque no cronometro
  Pausado --> Correndo: toque no cronometro
  Correndo --> Fora: Fechar ou Escape
  Pausado --> Fora: Fechar ou Escape
```

Ao entrar: pedir Fullscreen no elemento raiz da apresentação. Se a promise rejeitar ou a API não existir, aplicar a classe de tela cheia simulada (`position: fixed; inset: 0; z-index: 40; height: 100dvh; padding` com `safe-area`). Ao sair: `exitFullscreen` se o documento ainda estiver em tela cheia, e remover a classe simulada.

Cronômetro: ao entrar, acumulado 0 e relógio correndo. Pausar soma ao acumulado o trecho desde o último resume. Retomar grava um novo instante. Exibir com `requestAnimationFrame` ou intervalo de 250 ms. Abaixo de 1 hora, `mm:ss` com dois dígitos. A partir de 1 hora, `h:mm:ss`. Sair zera tudo.

Botões de tópico: próximo incrementa o índice e chama `scrollIntoView({ block: "start" })` na section. Anterior decrementa. Limites deixam o botão `disabled`. O índice ativo da apresentação também muda se a pessoa rolar, pela mesma regra do observer. O próximo comando de botão usa o índice já atualizado pela rolagem.

Barra de zoom e botões ficam fora do fluxo do texto, por cima, com `padding-bottom` da leitura de pelo menos 128px mais `safe-area-inset-bottom`.

### Zoom

| Constante | Valor |
| --- | --- |
| mínimo | 16 px |
| máximo | 40 px |
| padrão | 18 px |
| passo dos botões e do Ctrl+roda | 2 px |
| chave `localStorage` | `verso.readingFontSize` |

A área de leitura usa `font-size: var(--reading-font-size)` no conteúdo renderizado. Não usar `transform: scale`. Valor guardado inválido volta ao padrão.

Pinça: Pointer Events na área de leitura. Com dois ponteiros ativos, calcular a distância inicial e o tamanho inicial; no movimento, `clamp(round(tamanhoInicial * distanciaAtual / distanciaInicial))`. Soltar os ponteiros grava o `localStorage`. Com um ponteiro, a rolagem vertical segue normal (`touch-action: pan-y` enquanto houver um ponteiro; durante dois ponteiros, `preventDefault` no movimento). Ctrl+roda, ou Meta+roda, altera pelo passo e chama `preventDefault`.

### Gaveta

Presente na visualização e na apresentação de uma nota já criada. As citações saem de `parseCitations(topic.markdown)`. Cada citação é juntada, no navegador, a um item de `document.passages`: mesma `abbrev`, mesmo `chapter`, mesmo `start` e mesmo `end`. Se a citação tiver `version`, ela também precisa coincidir. Citação natural, com `version` nula, casa com a passagem embutida da mesma referência, qualquer que seja a versão gravada na criação. Sem item correspondente (citação ainda não salva), a gaveta mostra o rótulo montado pelo catálogo e "O texto será buscado quando a nota for salva."

Alça sempre visível. Texto da alça: "Nenhum versículo neste tópico" ou "N versículos" / "1 versículo", contando passagens (não cada versículo do intervalo). Clique alterna aberta/fechada. Arrastar: se ao soltar a altura passou de 30% da altura aberta, fica aberta; senão, fecha. Aberta: `min(50vh, 420px)`, rolagem interna.

Cada passagem encontrada mostra o rótulo e os versículos embutidos. Rótulo: `{book_name} {chapter}` no capítulo inteiro; `{book_name} {chapter}:{start}` quando start = end; `{book_name} {chapter}:{start}-{end}` no intervalo. Se `version` da passagem for diferente da versão atual da conta, prefixar o slug em maiúsculas e um espaço: `ACF Salmos 23:1-6`.

Item com `error` preenchido mostra o rótulo e uma mensagem conforme o erro: `not_found`, `invalid_reference` e `too_many` têm texto próprio; erro temporário mostra "Não foi possível buscar o texto. Tentaremos de novo quando a nota for aberta." Ao abrir uma nota com `passages_pending`, o front chama `refresh` (o autosave espera) e mostra um toast com o resultado; sem pendência, nenhum toast. Capítulo inteiro longo (como Salmos 119) rola dentro da gaveta; não resumir.

Trocar de tópico só refaz esse cruzamento local. Não há estado "Carregando…" de rede.

### Vidro

Uma classe só, usada pelo cartão de entrada, cronômetro, botões de tópico, barra de zoom, gaveta e alça:

```css
.glass {
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .glass {
    background: rgba(15, 23, 42, 0.92);
  }
}
```

Tema escuro da página: fundo `#0b1220`, texto de leitura `#f8fafc`. `theme_color` e `background_color` da PWA: `#0f172a`.

Z-index: raiz da apresentação 40; cronômetro, barra, botões e gaveta 50.

### PWA

Manifest: `name` e `short_name` "Verso", `start_url` "/app", `scope` "/", `display` "standalone", ícones 192 e 512 em `any` e `maskable`. Service worker pré-cacheia o shell gerado pelo plugin. Runtime caching não inclui `/api/documents` nem `/api/folders`. Sem fallback que finja nota disponível offline.

## Catálogo de livros

Normativo. Aliases já em minúsculas. O matcher também põe o texto da nota em minúsculas com `toLocaleLowerCase("pt-BR")` e não remove acentos: `jo` é João e `jó` é Jó.

```json
[
  {"abbrev":"gn","name":"Gênesis","chapters":50,"aliases":["gênesis","genesis","gn","gen"]},
  {"abbrev":"ex","name":"Êxodo","chapters":40,"aliases":["êxodo","exodo","ex","êx"]},
  {"abbrev":"lv","name":"Levítico","chapters":27,"aliases":["levítico","levitico","lv","lev"]},
  {"abbrev":"nm","name":"Números","chapters":36,"aliases":["números","numeros","nm","num","núm"]},
  {"abbrev":"dt","name":"Deuteronômio","chapters":34,"aliases":["deuteronômio","deuteronomio","dt","deut"]},
  {"abbrev":"js","name":"Josué","chapters":24,"aliases":["josué","josue","js"]},
  {"abbrev":"jz","name":"Juízes","chapters":21,"aliases":["juízes","juizes","jz"]},
  {"abbrev":"rt","name":"Rute","chapters":4,"aliases":["rute","ruth","rt"]},
  {"abbrev":"1sm","name":"1 Samuel","chapters":31,"aliases":["1 samuel","1samuel","1 sm","1sm","i samuel","1º samuel","1ª samuel","primeiro samuel"]},
  {"abbrev":"2sm","name":"2 Samuel","chapters":24,"aliases":["2 samuel","2samuel","2 sm","2sm","ii samuel","2º samuel","2ª samuel","segundo samuel"]},
  {"abbrev":"1rs","name":"1 Reis","chapters":22,"aliases":["1 reis","1reis","1 rs","1rs","i reis","1º reis","1ª reis","primeiro reis"]},
  {"abbrev":"2rs","name":"2 Reis","chapters":25,"aliases":["2 reis","2reis","2 rs","2rs","ii reis","2º reis","2ª reis","segundo reis"]},
  {"abbrev":"1cr","name":"1 Crônicas","chapters":29,"aliases":["1 crônicas","1 cronicas","1 cr","1cr","i crônicas","i cronicas","1º crônicas","1ª crônicas"]},
  {"abbrev":"2cr","name":"2 Crônicas","chapters":36,"aliases":["2 crônicas","2 cronicas","2 cr","2cr","ii crônicas","ii cronicas","2º crônicas","2ª crônicas"]},
  {"abbrev":"ed","name":"Esdras","chapters":10,"aliases":["esdras","ed","esd"]},
  {"abbrev":"ne","name":"Neemias","chapters":13,"aliases":["neemias","ne"]},
  {"abbrev":"et","name":"Ester","chapters":10,"aliases":["ester","et"]},
  {"abbrev":"job","name":"Jó","chapters":42,"aliases":["jó","job"]},
  {"abbrev":"sl","name":"Salmos","chapters":150,"aliases":["salmos","salmo","sl"]},
  {"abbrev":"pv","name":"Provérbios","chapters":31,"aliases":["provérbios","proverbios","pv","prov"]},
  {"abbrev":"ec","name":"Eclesiastes","chapters":12,"aliases":["eclesiastes","ec","ecl"]},
  {"abbrev":"ct","name":"Cânticos","chapters":8,"aliases":["cânticos","canticos","cantares","cântico","cantico","ct"]},
  {"abbrev":"is","name":"Isaías","chapters":66,"aliases":["isaías","isaias","is"]},
  {"abbrev":"jr","name":"Jeremias","chapters":52,"aliases":["jeremias","jr"]},
  {"abbrev":"lm","name":"Lamentações","chapters":5,"aliases":["lamentações","lamentacoes","lm","lam"]},
  {"abbrev":"ez","name":"Ezequiel","chapters":48,"aliases":["ezequiel","ez"]},
  {"abbrev":"dn","name":"Daniel","chapters":12,"aliases":["daniel","dn"]},
  {"abbrev":"os","name":"Oséias","chapters":14,"aliases":["oséias","oseias","os"]},
  {"abbrev":"jl","name":"Joel","chapters":3,"aliases":["joel","jl"]},
  {"abbrev":"am","name":"Amós","chapters":9,"aliases":["amós","amos","am"]},
  {"abbrev":"ob","name":"Obadias","chapters":1,"aliases":["obadias","ob","obd"]},
  {"abbrev":"jn","name":"Jonas","chapters":4,"aliases":["jonas","jn"]},
  {"abbrev":"mq","name":"Miquéias","chapters":7,"aliases":["miquéias","miqueias","mq","miq"]},
  {"abbrev":"na","name":"Naum","chapters":3,"aliases":["naum","na"]},
  {"abbrev":"hc","name":"Habacuque","chapters":3,"aliases":["habacuque","hc","hab"]},
  {"abbrev":"sf","name":"Sofonias","chapters":3,"aliases":["sofonias","sf","sof"]},
  {"abbrev":"ag","name":"Ageu","chapters":2,"aliases":["ageu","ag"]},
  {"abbrev":"zc","name":"Zacarias","chapters":14,"aliases":["zacarias","zc","zac"]},
  {"abbrev":"ml","name":"Malaquias","chapters":4,"aliases":["malaquias","ml","mal"]},
  {"abbrev":"mt","name":"Mateus","chapters":28,"aliases":["mateus","mt"]},
  {"abbrev":"mc","name":"Marcos","chapters":16,"aliases":["marcos","mc"]},
  {"abbrev":"lc","name":"Lucas","chapters":24,"aliases":["lucas","lc"]},
  {"abbrev":"jo","name":"João","chapters":21,"aliases":["joão","joao","jo"]},
  {"abbrev":"at","name":"Atos","chapters":28,"aliases":["atos dos apóstolos","atos dos apostolos","atos","at"]},
  {"abbrev":"rm","name":"Romanos","chapters":16,"aliases":["romanos","rm","rom"]},
  {"abbrev":"1co","name":"1 Coríntios","chapters":16,"aliases":["1 coríntios","1 corintios","1 co","1co","1 cor","1cor","i coríntios","i corintios","1ª coríntios","1º coríntios","primeira coríntios"]},
  {"abbrev":"2co","name":"2 Coríntios","chapters":13,"aliases":["2 coríntios","2 corintios","2 co","2co","2 cor","2cor","ii coríntios","ii corintios","2ª coríntios","2º coríntios","segunda coríntios"]},
  {"abbrev":"gl","name":"Gálatas","chapters":6,"aliases":["gálatas","galatas","gl","gal"]},
  {"abbrev":"ef","name":"Efésios","chapters":6,"aliases":["efésios","efesios","ef"]},
  {"abbrev":"fp","name":"Filipenses","chapters":4,"aliases":["filipenses","fp","flp"]},
  {"abbrev":"cl","name":"Colossenses","chapters":4,"aliases":["colossenses","cl","col"]},
  {"abbrev":"1ts","name":"1 Tessalonicenses","chapters":5,"aliases":["1 tessalonicenses","1 ts","1ts","1 tess","i tessalonicenses","1ª tessalonicenses","1º tessalonicenses"]},
  {"abbrev":"2ts","name":"2 Tessalonicenses","chapters":3,"aliases":["2 tessalonicenses","2 ts","2ts","2 tess","ii tessalonicenses","2ª tessalonicenses","2º tessalonicenses"]},
  {"abbrev":"1tm","name":"1 Timóteo","chapters":6,"aliases":["1 timóteo","1 timoteo","1 tm","1tm","i timóteo","i timoteo","1ª timóteo","1º timóteo"]},
  {"abbrev":"2tm","name":"2 Timóteo","chapters":4,"aliases":["2 timóteo","2 timoteo","2 tm","2tm","ii timóteo","ii timoteo","2ª timóteo","2º timóteo"]},
  {"abbrev":"tt","name":"Tito","chapters":3,"aliases":["tito","tt"]},
  {"abbrev":"fm","name":"Filemom","chapters":1,"aliases":["filemom","filemon","fm","flm"]},
  {"abbrev":"hb","name":"Hebreus","chapters":13,"aliases":["hebreus","hb","heb"]},
  {"abbrev":"tg","name":"Tiago","chapters":5,"aliases":["tiago","tg"]},
  {"abbrev":"1pe","name":"1 Pedro","chapters":5,"aliases":["1 pedro","1 pe","1pe","i pedro","1ª pedro","1º pedro"]},
  {"abbrev":"2pe","name":"2 Pedro","chapters":3,"aliases":["2 pedro","2 pe","2pe","ii pedro","2ª pedro","2º pedro"]},
  {"abbrev":"1jo","name":"1 João","chapters":5,"aliases":["1 joão","1 joao","1 jo","1jo","i joão","i joao","1ª joão","1º joão"]},
  {"abbrev":"2jo","name":"2 João","chapters":1,"aliases":["2 joão","2 joao","2 jo","2jo","ii joão","ii joao","2ª joão","2º joão"]},
  {"abbrev":"3jo","name":"3 João","chapters":1,"aliases":["3 joão","3 joao","3 jo","3jo","iii joão","iii joao","3ª joão","3º joão"]},
  {"abbrev":"jd","name":"Judas","chapters":1,"aliases":["judas","jd"]},
  {"abbrev":"ap","name":"Apocalipse","chapters":22,"aliases":["apocalipse","ap","apoc"]}
]
```

Nenhum alias se repete entre livros. Não criar alias nu de livro numerado (`samuel`, `coríntios`, `joão` sem número continua sendo o evangelho). Não criar alias `jo` para Jó.

## Parser de citações

Função pura no front: `parseCitations(markdown: string): ParsedCitation[]`. A versão da conta entra só na hora do `POST`, para citações naturais (`version` nula no parse). A forma explícita já traz a versão.

```ts
type ParsedCitation = {
  version: string | null;
  abbrev: string;
  chapter: number;
  start: number | null;
  end: number | null;
  index: number;
};
```

Passos:

1. Trabalhar numa cópia mascarada: cercas ``` e ~~~, código inline entre crases simples, e comentários HTML `<!-- -->` viram espaços do mesmo comprimento, para os índices originais se manterem.
2. Achar formas explícitas e substituí-las por espaços do mesmo comprimento, para o passo natural não contá-las de novo.

O texto da forma natural e da forma explícita é comparado já em minúsculas. A expressão natural usa as flags `g` e `u`. A flag `u` é obrigatória para `\p{L}` e para o lookbehind. Node 22 e os navegadores atuais aceitam os dois.

Forma explícita:

```text
\[\[([a-z0-9]{2,20}):([a-z0-9]{1,8}):(\d{1,3})(?::(\d{1,3})(?:-(\d{1,3}))?)?\]\]
```

Exemplos válidos: `[[acf:sl:23:1-6]]`, `[[nvi:jo:3:16]]`, `[[nvi:sl:23]]`. Abreviação tem de existir no catálogo. Capítulo dentro de 1..`chapters`. Versículo, se houver, é no mínimo 1. Capítulo inteiro quando o quarto grupo não existe (`start` e `end` nulos).

3. Forma natural, sobre o texto já mascarado e em minúsculas. Construir uma alternância com todos os aliases, do mais longo para o mais curto, cada um escapado como literal. Entre aliases de mesmo tamanho, não importa a ordem, exceto que o par `jó` e `jo` funciona nos dois sentidos porque a olhada à frente exige que o alias termine onde acaba o token.

```text
(?<![\p{L}\p{N}])(?:ALIAS)\.?(?![\p{L}\p{N}])\s*(\d{1,3})(?:\s*[:.]\s*(\d{1,3})(?:\s*[-–—]\s*(\d{1,3}))?)?
```

O `\.?` cobre `Sl. 23`. O separador de capítulo e versículo é `:` ou `.`. O travessão do intervalo pode ser `-`, `–` ou `—`.

4. Se a forma natural não capturou versículo, só aceite como capítulo inteiro quando o que vem imediatamente depois do número, sem consumir letras, casa com fim do texto, ou com espaços opcionais seguidos de fim, ou com espaços opcionais seguidos de um destes: `, . ; ! ? ) ] } ” " '`. Assim `Salmos 23` e `(Gn 1)` entram, e `João 3 vezes` fica de fora. A forma com `:` ou `.` e versículo não passa por esse filtro.

5. Descartar capítulo fora de 1..`chapters` ou versículo 0. Se `end < start`, trocar. Se há `start` e não há `end`, `end = start`.

6. Ordenar por `index`. Remover duplicatas da chave `version|abbrev|chapter|start|end`, mantendo a primeira. `version` nula entra na chave como vazio.

### Vetores que o parser tem de cumprir

Entradas que produzem uma citação:

| Texto | Resultado |
| --- | --- |
| `João 3:16` | `jo` 3:16-16, versão nula |
| `Jo 3.16` | `jo` 3:16-16 |
| `João 3:16-18` | `jo` 3:16-18 |
| `1 Coríntios 13:4-7` | `1co` 13:4-7 |
| `1 Co 13:4` | `1co` 13:4 |
| `1Co 13:4` | `1co` 13:4 |
| `Sl 23` | `sl` 23, capítulo inteiro |
| `Salmos 23:1` | `sl` 23:1-1 |
| `Gn 1:1-3` | `gn` 1:1-3 |
| `Jó 1:21` | `job` 1:21-21 |
| `Job 1:21` | `job` 1:21-21 |
| `leia João 3:16 hoje` | uma citação `jo` 3:16-16 |
| `[[acf:sl:23:1-6]]` | versão `acf`, `sl` 23:1-6 |
| `[[nvi:sl:23]]` | versão `nvi`, `sl` 23 inteiro |
| `I João 1:9` | `1jo` 1:9-9 |
| `2ª Timóteo 3:16` | `2tm` 3:16-16 |
| `Sl. 23:1` | `sl` 23:1-1 |
| `(Gn 1)` | `gn` 1 inteiro |
| `João 3:16 e João 3:16` | uma só citação |

Entradas que não produzem citação:

| Texto | Motivo |
| --- | --- |
| `João 3 vezes` | número seguido de palavra, sem versículo |
| `` `João 3:16` `` | código inline |
| bloco cercado com `João 3:16` | cerca |
| `Coríntios 13:4` | livro numerado sem o número |
| `João 99:1` | capítulo acima de 21 |
| `Jo 3:16` | é João, não Jó |

### Vetor de tópicos

```markdown
intro

# A
texto a João 3:16

## B
texto b

# C
```

Tópicos, nesta ordem: "Início" com `intro`; "A" contendo a citação `jo` 3:16; "B"; "C". A partir de "A", o próximo tópico é "B".

Um `#` dentro de uma cerca não cria tópico.

## Árvore de código

```text
verso/
  .env.example
  compose.yaml
  README.md
  docs/
    ESPECIFICACAO.md
    ARQUITETURA.md
    PLANO.md
  apps/
    api/
      pyproject.toml
      app/
        main.py
        config.py
        db.py
        models.py
        security.py
        deps.py
        errors.py
        routers/
          auth.py
          folders.py
          documents.py
        services/
          bible.py
          citations.py
          titles.py
      migrations/
      tests/
        test_auth.py
        test_isolation.py
        test_bible_slice.py
    web/
      package.json
      vite.config.ts
      src/
        app.html
        routes/
          +page.svelte
          app/
            +layout.svelte
            +layout.ts
            +page.svelte
            pastas/[id]/+page.svelte
            notas/nova/+page.svelte
            notas/[id]/+page.svelte
        lib/
          api.ts
          books.ts
          topics.ts
          citations.ts
          glass.css
          components/
            DocumentGrid.svelte
            MarkdownView.svelte
            ZoomBar.svelte
            VerseDrawer.svelte
            Presentation.svelte
      static/
```

`books.ts` exporta o catálogo JSON deste arquivo, sem alteração de abreviação, nome, capítulos ou aliases.

`services/bible.py` é chamado somente por `POST /api/documents`. Contém o cliente HTTP, o cache e o recorte. A validação de abreviação e capítulo usa uma cópia do mesmo catálogo em `apps/api/app/books.py`. As duas cópias têm de ser iguais; o teste da fase 10 compara as listas de abreviações e de capítulos.

## Segurança

- Argon2id via `argon2-cffi`, parâmetros padrão da biblioteca.
- Cookie não lido por script da página.
- Markdown renderizado com HTML cru desligado.
- Consultas de pasta e nota sempre com `user_id` da sessão.
- Log da API não imprime `BIBLE_API_TOKEN`, senha nem cookie.
- Limite de 200_000 caracteres no corpo e 40 passagens resolvidas com o provedor na criação da nota.

## O que esta arquitetura não abre

GitHub, offline das notas, compartilhamento, busca, lixeira, tema claro, PDF, mover nota de pasta, nova consulta bíblica depois da criação e qualquer provedor bíblico com contrato diferente do descrito aqui.
