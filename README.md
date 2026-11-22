# Verso

Notas de pregação em Markdown, com apresentação em tela cheia, cronômetro, zoom e gaveta de versículos.
A especificação está em [docs/ESPECIFICACAO.md](docs/ESPECIFICACAO.md), o desenho técnico em
[docs/ARQUITETURA.md](docs/ARQUITETURA.md) e a ordem de construção em [docs/PLANO.md](docs/PLANO.md).

## Subir o ambiente

1. Copie o arquivo de exemplo:

   ```sh
   cp .env.example .env
   ```

2. Suba os três serviços (`postgres`, `api`, `web`):

   ```sh
   docker compose up --build
   ```

3. Abra `http://localhost:5173`.

O health da API fica em `http://localhost:8000/api/health` e deve devolver `{ "status": "ok" }`.
As migrations do Alembic rodam sozinhas quando o serviço `api` sobe.

Se o `package.json` do front mudar, recrie o volume de `node_modules`:

```sh
docker compose up --build -V web
```

## Criar a primeira conta

O primeiro cadastro é protegido por `BOOTSTRAP_SECRET` e só pode ser realizado uma vez.
Configure um segredo aleatório forte no ambiente antes de iniciar a API e envie-o uma única vez no header `X-Bootstrap-Secret`.
Não envie o campo `invite` nessa primeira criação.

Em produção, substitua `<DOMINIO>` e `<BOOTSTRAP_SECRET>` pelos valores do servidor:

```sh
curl -i -X POST "https://<DOMINIO>/api/auth/register" \
  -H "Content-Type: application/json" \
  -H "X-Bootstrap-Secret: <BOOTSTRAP_SECRET>" \
  -d '{"name":"Administrador","email":"admin@exemplo.com","password":"SENHA_FORTE"}'
```

Uma resposta `201 Created` confirma a criação e consome o bootstrap definitivamente. Depois, entre em Verso e use o recurso de convites para cadastrar novas contas.

Para contas seguintes, o cadastro pela interface exige o convite gerado pelo primeiro usuário:

```text
https://<DOMINIO>/cadastro?convite=<TOKEN_DO_CONVITE>
```

## Rodar localmente com SQLite (sem Docker)

Requisitos: Python 3.12+ e Node 22.14+ (o `@vite-pwa/sveltekit` não carrega no Node 20; com nvm,
`nvm install 22` e `nvm use 22`). O pnpm vem pelo corepack.

Com GNU Make (no Windows: `winget install ezwinports.make`), da raiz do repositório:

```sh
make install   # venv da API + pnpm install
make dev       # migra o SQLite e sobe API (:8000) e front (:5173)
make test      # pytest + vitest
```

`make` sem argumentos lista os alvos. Sem Make, os passos equivalentes são:

API, num terminal (PowerShell):

```powershell
cd apps/api
py -3.14 -m venv .venv            # ou qualquer Python 3.12+
.\.venv\Scripts\python -m pip install -e ".[dev]"
Copy-Item .env.example .env       # opcional: sem .env o padrão já é sqlite:///./verso.db
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

O banco fica em `apps/api/verso.db`. Para recomeçar do zero, pare a API, apague `verso.db*` e rode
`alembic upgrade head` de novo.

Front, noutro terminal:

```powershell
cd apps/web
corepack enable
pnpm install
pnpm dev
```

Abra `http://localhost:5173`. O Vite encaminha `/api` para `http://127.0.0.1:8000` (mude com
`API_PROXY_TARGET`).

Testes locais: `.\.venv\Scripts\python -m pytest` em `apps/api` usa um SQLite temporário, sem tocar em
`verso.db`; `pnpm test` em `apps/web`. O Compose continua com Postgres; o mesmo código e as mesmas
migrations servem aos dois bancos.

## Marcações na nota

Uma nota é Markdown. Duas marcações têm efeito além do texto: a citação de versículo e o tempo da apresentação.

```markdown
[[tempo 15m alerta 2m]]

# A graça que basta

O amor de Deus cabe num versículo: João 3:16.

O salmo inteiro, numa versão escolhida: [[acf:sl:23]].
```

### Versículos

A citação pode ser escrita como no texto:

- `João 3:16` — um versículo
- `João 3:16-18` — um intervalo
- `Salmos 23` — o capítulo inteiro
- `Jo 3.16` — abreviação; `:` e `.` separam capítulo e versículo

A forma explícita fixa a versão: `[[versão:livro:capítulo]]` ou `[[versão:livro:capítulo:início-fim]]`. Exemplos: `[[nvi:jo:3:16]]`, `[[acf:sl:23:1-6]]`. A abreviação do livro é a do catálogo (`jo`, `sl`, `1co`).

Na forma natural, a versão é a da conta. Na explícita, vale a versão escrita na marcação. Cerca de código, crase simples e comentário HTML não viram citação. `[[tempo ...]]` também não: é o cronômetro.

Na visualização e na apresentação, a gaveta do tópico ativo lista as passagens citadas naquele trecho.

### Cronômetro

Sem marcação, o relógio da apresentação começa em `00:00` e conta para a frente. Com uma linha própria, fora de cerca de código, ele conta para trás:

```markdown
[[tempo 15m alerta 2m]]
```

`15m` é o alvo: o relógio abre em `15:00`. `alerta 2m` é o restante a partir do qual os dígitos ficam vermelhos e pulsam. Depois do zero a contagem continua, com sinal negativo (`-00:01`).

A duração aceita `15m`, `15min`, `90s`, `1h30m` e `1h 30m`. O alvo precisa ser maior que zero. `[[tempo 15m]]` conta para trás sem mudar a cor. `alerta 0s` pinta o relógio ao chegar em `00:00`.

A primeira linha válida vale. Ela some na visualização e na apresentação e continua na fonte. Uma linha inválida permanece visível. Toque ou clique no relógio pausa e retoma. Sair da apresentação zera o tempo.

## Versículos

O servidor busca o texto bíblico num provedor compatível com a ABíbliaDigital e o grava na nota:

- na criação (`POST /api/documents`), para todas as citações;
- em cada salvamento que muda o texto (`PATCH`), só para citações que ainda não têm passagem;
- ao abrir a nota, se alguma passagem falhou por motivo temporário (provedor fora do ar, limite de
  requisições): o front chama `POST /api/documents/{id}/passages/refresh` e mostra um toast com o resultado.

Configure no `.env`:

- `BIBLE_API_BASE_URL`: base do provedor, sem barra no fim;
- `BIBLE_API_TOKEN`: token Bearer, opcional. Vazio, as requisições saem sem `Authorization` e o
  provedor aplica o limite anônimo, que é menor.

O token nunca chega ao navegador.

## Testes

API (pytest, contra um banco `verso_test` criado no mesmo Postgres do Compose):

```sh
docker compose run --rm api pytest
```

Front (Vitest: tópicos, citações, catálogo de livros e cálculo de zoom):

```sh
docker compose run --rm web pnpm test
```

## Produção local da PWA

O service worker só é registrado no build. Para conferir manifest e worker:

```sh
docker compose run --rm -p 4173:4173 web sh -c "pnpm build && pnpm preview --host 0.0.0.0"
```

e abra `http://localhost:4173`.

## Pinça sem tela de toque

A pinça usa Pointer Events com dois ponteiros `touch`/`pen`. Num desktop sem toque, ela foi exercitada
emulando toque no navegador (DevTools, modo dispositivo) e o cálculo
(`tamanho inicial × distância atual ÷ distância inicial`, com os limites 16–40) é coberto em
`apps/web/src/lib/zoom.test.ts`. `Ctrl` + roda (ou `Cmd` + roda) altera a fonte no desktop.

## Versionamento

Verso usa [Semantic Versioning](https://semver.org/) no formato `MAJOR.MINOR.PATCH`, com tags Git `vMAJOR.MINOR.PATCH`.

- `MAJOR`: mudança incompatível, remoção de API ou migração que exige ação manual;
- `MINOR`: nova funcionalidade compatível com o comportamento existente;
- `PATCH`: correção, ajuste de segurança ou melhoria interna sem quebra.

A versão do produto deve ser atualizada em conjunto em `apps/api/pyproject.toml` e `apps/web/package.json`. Antes de publicar uma versão, execute os testes, confira os builds Docker e crie a tag Git correspondente.

Exemplos: corrigir o cálculo do cronômetro é um `PATCH`; adicionar um novo tipo de convite opcional é um `MINOR`; mudar um formato persistido sem compatibilidade é um `MAJOR`.

A API e o frontend são versionados separadamente: atualize `apps/api/pyproject.toml` apenas para mudanças da API e `apps/web/package.json` apenas para mudanças do frontend. Ambos podem ter números SemVer diferentes no mesmo repositório.

Uma tag Git `vX.Y.Z` publica apenas a aplicação cujo manifesto tiver exatamente `X.Y.Z`. Antes de publicar, execute os testes, confira os builds Docker e crie a tag correspondente à aplicação alterada.
