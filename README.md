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
