# Especificação — Verso

Data: 4 de novembro de 2026.
Estado: normativa para a versão 1.
Leia também [ARQUITETURA.md](ARQUITETURA.md) e [PLANO.md](PLANO.md).

## Como um agente deve usar este arquivo

1. Leia este arquivo por inteiro antes de escrever código.
2. Leia [ARQUITETURA.md](ARQUITETURA.md) antes de escolher bibliotecas, rotas, tabelas ou formato de citação.
3. Execute [PLANO.md](PLANO.md) na ordem das fases. Não antecipe uma fase dentro de outra, salvo onde o próprio plano manda criar um componente compartilhado.
4. Em conflito de comportamento de produto (o que a pessoa vê e o que o sistema garante), este arquivo vence.
5. Em conflito de desenho técnico (rotas, tabelas, algoritmos, pastas), a arquitetura vence.
6. Em conflito de ordem de execução, o plano vence.
7. Não invente funcionalidade listada em [Fora de escopo](#fora-de-escopo). Se um requisito daqui não estiver coberto pela arquitetura, pare e registre a lacuna no código apenas como comentário de tarefa no documento de arquitetura correspondente — não preencha a lacuna com uma decisão nova.
8. Textos de interface ficam em português do Brasil.
9. Não copie o texto de traduções bíblicas para o repositório. O texto que a pessoa vê fica gravado na nota, capturado do provedor na criação, nas edições (citações novas) e ao abrir a nota (passagens que falharam), conforme a arquitetura. Testes usam frases sintéticas.

## Problema

Quem prega ou dirige uma célula precisa escrever a mensagem em Markdown, levá-la no celular ou no computador, apresentá-la em tela cheia com o tempo à vista, ampliar a fonte no meio do culto e consultar na hora os versículos citados no tópico que está na tela.

Há mais de uma pessoa usando o sistema. Cada pessoa vê somente as próprias pastas e notas.

## Atores

- **Pessoa autenticada.** Cria pastas e notas, edita, apresenta e consulta versículos.
- **Visitante.** Vê a tela de entrada e pode criar uma conta. Não acessa notas.
- **Operador.** Sobe a aplicação e configura o token do provedor bíblico. Não tem tela própria nesta versão.

## Nome

- Repositório e Compose: `verso`.
- Nome visível e `short_name` da PWA: **Verso**.

## Fluxo principal

1. A pessoa abre a aplicação e entra, ou cria uma conta na mesma tela.
2. Cai na grade da pasta raiz: pastas e notas. Cada nota mostra título e data de criação.
3. Entra numa pasta, ou abre uma nota.
4. “Nova nota” abre um rascunho na pasta atual. A pessoa escreve o Markdown e confirma em “Criar nota”. Nesse instante o servidor grava a nota e embute o texto dos versículos citados.
5. Na nota já criada, alterna entre edição da fonte Markdown e visualização renderizada. A gravação seguinte altera título e Markdown e não consulta o provedor de novo.
6. Pode entrar em apresentação: visualização em tela cheia, cronômetro, avanço de tópico, zoom e gaveta de versículos do tópico ativo, lendo o texto já embutido.

## Glossário

- **Nota.** Documento Markdown de uma pessoa, com título, data de criação, pasta opcional e as passagens embutidas na criação.
- **Passagem embutida.** Texto dos versículos de uma citação, gravado dentro da nota no momento em que ela é criada. Abrir, editar, visualizar e apresentar leem esse texto. Não há nova consulta ao provedor.
- **Pasta.** Agrupador nomeado. Pode conter pastas e notas. A raiz não é uma pasta persistida: é a ausência de pasta pai.
- **Tópico.** Trecho que começa num heading Markdown (`#` a `######`) e segue até o heading seguinte, de qualquer nível. O miolo antes do primeiro heading é o tópico **Início**. A subárvore de headings não define o tópico: o próximo heading, mesmo de nível menor, encerra o tópico atual.
- **Apresentação.** Estado de tela cheia da nota aberta, sempre na visualização renderizada. Não é outra nota nem outra rota.
- **Citação.** Referência a livro, capítulo e, quando houver, intervalo de versículos, reconhecida pela gramática da arquitetura.
- **Provedor bíblico.** HTTP compatível com o contrato da ABíbliaDigital descrito na arquitetura. O navegador não fala com ele.

## Requisitos funcionais

Cada requisito inclui o critério de aceite. Os nomes de campo e de rota estão na arquitetura.

### RF-001 — Criar conta

A tela de entrada oferece “Criar conta” no mesmo cartão do login. Os campos são nome, e-mail e senha. Senha com no mínimo 8 caracteres. E-mail é único, sem diferenciar maiúsculas. Conta criada já entra na aplicação.

Aceite: e-mail repetido permanece na tela e explica que a conta já existe. Senha curta não é enviada como sucesso.

### RF-002 — Entrar

Campos e-mail e senha, botão “Entrar”. Credencial válida abre a grade da raiz. Credencial inválida permanece na tela, com mensagem única para e-mail desconhecido e senha errada.

### RF-003 — Sair

A área autenticada tem ação “Sair”. Depois dela, as rotas `/app` voltam para a tela de entrada.

### RF-004 — Isolamento

Pastas e notas de uma pessoa são invisíveis para as outras. Pedido com id alheio responde como recurso inexistente.

Aceite: duas contas, cada uma com uma nota; a segunda não lista, não abre, não altera e não apaga a nota da primeira.

### RF-005 — Pastas

A pessoa cria, renomeia e apaga pastas dentro da pasta atual, inclusive na raiz. Pastas aninham até a profundidade máxima definida na arquitetura. A pasta abre outra grade, só com o conteúdo dela. Há trilha de ancestrais até a raiz.

Apagar pasta que ainda tem pasta ou nota filha não apaga nada e explica que é preciso esvaziar antes.

### RF-006 — Grade

A grade da pasta atual mostra primeiro as pastas (nome) e depois as notas (título e data de criação, formato `dd/MM/yyyy` em `pt-BR`). Há ações “Nova pasta” e “Nova nota”. Grade vazia mostra um estado vazio com essas ações.

A grade reflow: uma coluna em viewport estreita, duas a partir de 640px, três a partir de 1024px.

### RF-007 — Criar e abrir nota

“Nova nota” abre um rascunho local da pasta atual, em edição, com título inicial “Sem título”. O rascunho fica neste navegador até a pessoa confirmar “Criar nota”. Essa confirmação é o único momento em que a nota nasce no servidor e em que o texto dos versículos é buscado e embutido. O título inicial gravado segue a regra de título vazio.

### RF-008 — Edição

O modo edição mostra a fonte Markdown num editor de código (CodeMirror 6), mais um campo de título no topo. Não é editor WYSIWYG.

### RF-009 — Visualização

O modo visualização mostra o Markdown renderizado (títulos, listas, ênfase, citações em bloco, código, links). Um controle alterna edição e visualização sem perder o texto que ainda não foi gravado.

### RF-010 — Gravação automática

Depois que a nota existe no servidor, alterar título ou corpo agenda uma gravação 800 ms após a última alteração. A tela indica “Salvando…”, “Salvo” ou “Erro ao salvar”. Erro permite nova tentativa na alteração seguinte. Essa gravação não altera as passagens embutidas e não chama o provedor. O rascunho anterior a “Criar nota” não usa essa gravação no servidor.

### RF-011 — Título e data

A grade usa o título gravado e a data de criação. O título é o campo do topo. Se a pessoa deixar o campo vazio, a gravação usa o texto do primeiro heading do corpo; se não houver heading, usa “Sem título”. A data exibida não muda quando a nota é editada.

### RF-012 — Apresentação em tela cheia

Na nota, “Apresentar” entra em tela cheia na visualização renderizada. Sair volta para a visualização (não para a edição), na mesma nota.

Onde a Fullscreen API funcionar, usá-la no elemento da apresentação. Onde falhar, inclusive no Safari/iOS, usar tela cheia simulada: elemento fixo, `100dvh`, acima do resto da interface, respeitando `safe-area`. Escape e um botão “Fechar” saem da apresentação.

### RF-013 — Cronômetro

Ao entrar na apresentação, um cronômetro visível começa em `00:00` e conta o tempo decorrido. Toque ou clique pausa e retoma. Tempo pausado não entra na contagem. A partir de 60 minutos o formato passa a `h:mm:ss`. Sair da apresentação zera o cronômetro.

### RF-014 — Avançar e voltar tópico

Na apresentação, um botão flutuante grande, no canto inferior direito, acima da barra de zoom, leva ao próximo tópico e rola o heading correspondente para o topo da área de leitura. No último tópico o botão fica inativo.

Um botão menor, ao lado, volta ao tópico anterior. No primeiro tópico ele fica inativo.

Os dois botões têm nome acessível (“Próximo tópico” e “Tópico anterior”) e não cobrem a barra de zoom nem o cronômetro.

### RF-015 — Tópico

A divisão de tópicos segue o glossário. Headings dentro de bloco de código não criam tópico. Documento sem heading tem um único tópico, “Início”.

### RF-016 — Zoom por botões

Barra flutuante na base da área de leitura, com diminuir e aumentar a fonte. O texto reflui (muda o tamanho da fonte). Não usar `transform: scale`. Limites e passo estão na arquitetura. A preferência fica em `localStorage` e vale para as notas seguintes neste navegador.

A área de leitura reserva espaço inferior para a barra, os botões de tópico e a alça da gaveta, para a última linha continuar legível.

### RF-017 — Zoom por pinça

Na área de leitura, em tela de toque, o gesto de pinça altera a mesma fonte dos botões, com os mesmos limites. A rolagem vertical com um dedo continua possível. `Ctrl` + roda do mouse também altera a fonte, para trackpad.

### RF-018 — Gaveta de versículos

Painel inferior no estilo gaveta, na visualização e na apresentação. A alça mostra a quantidade de citações do tópico ativo. Arrastar a alça ou clicar nela abre e fecha. Aberta, a gaveta lista as passagens daquele tópico, com referência e o texto embutido de cada versículo. O painel rola por dentro quando o texto é longo.

Tópico sem citação: alça com “Nenhum versículo neste tópico” e, ao abrir, estado vazio. Citação nova tem o texto buscado quando a nota é salva; até lá, a gaveta mostra “O texto será buscado quando a nota for salva.” Quando a busca falha por motivo temporário (provedor fora do ar, limite de requisições), a gaveta avisa e a busca é repetida ao abrir a nota, para edição ou visualização, com um toast informando o resultado. Passagem que já tem texto não é buscada de novo. A nota continua editável, visível e apresentável.

### RF-019 — Citação ligada ao tópico ativo

A gaveta usa somente as citações do tópico ativo, não da nota inteira, e completa cada uma com a passagem embutida de mesma referência. Trocar de tópico troca a lista sem nenhuma chamada de rede.

Na visualização, o tópico ativo é o que ocupa o topo da área de leitura enquanto a pessoa rola. Na apresentação, o tópico ativo é o último alcançado pelo botão ou pela rolagem.

A gramática aceita formas naturais (`João 3:16`, `Jo 3.16`, `1 Coríntios 13:4-7`, `Sl 23`, `Gn 1:1-3`, `Jó 1:21`) e a forma explícita com versão (`[[acf:sl:23:1-6]]`). A lista normativa de livros, aliases e capítulos está na arquitetura. Citação dentro de código inline ou cercado não entra na gaveta.

### RF-020 — Versão bíblica

Cada conta tem uma versão padrão, inicial `nvi`. Um seletor na área autenticada, visível na grade, altera essa versão para as próximas criações. Na criação, citações naturais gravam o texto nessa versão; a forma `[[versão:...]]` grava a versão escrita nela. Mudar o seletor depois não reescreve as passagens já embutidas. O seletor não consulta o provedor.

### RF-021 — PWA

A aplicação é instalável. O manifest pede `display: standalone`, nome “Verso”, `start_url` da área autenticada, cor de tema escura e ícones 192 e 512. Um service worker guarda o shell (HTML de entrada, JS, CSS, ícones). Não guarda o corpo das notas como modo offline.

### RF-022 — Celular e desktop

Os fluxos de entrar, grade, pasta, editar, visualizar, apresentar, zoom e gaveta funcionam em viewport de 390px de largura e em viewport de 1280px. Controles flutuantes respeitam `safe-area-inset`. Não há uma interface paralela só para desktop: é o mesmo fluxo, com a grade refluindo.

### RF-023 — Vidro jateado

Cronômetro, botões de tópico, barra de zoom, gaveta e a alça da gaveta compartilham um único tratamento visual de vidro: fundo translúcido, borda clara suave, `backdrop-filter` com desfoque. Sem suporte a `backdrop-filter`, o fundo fica opaco o bastante para o texto do controle continuar legível. O cartão da tela de entrada usa o mesmo tratamento.

### RF-024 — Apagar nota

A nota pode ser apagada, com confirmação, e a pessoa volta à pasta onde ela estava. A exclusão é definitiva.

### RF-025 — Tema

A versão 1 tem um tema escuro único, com texto de leitura em alto contraste na apresentação. Não há seletor de tema.

## Requisitos não funcionais

### RNF-001 — Sessão e senha

Senha armazenada com Argon2id. Sessão em cookie `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` quando o ambiente pede. O cookie não é legível por JavaScript da página.

### RNF-002 — Token do provedor

O token da ABíbliaDigital existe só em variável de ambiente do servidor. O front não o recebe, não o embute e não chama o host do provedor.

### RNF-003 — Capítulo em uma ida

Durante a criação da nota, um intervalo (`João 3:16-18`) e várias citações do mesmo capítulo geram no máximo uma busca externa daquele capítulo. O recorte dos versículos é local e o resultado fica dentro da nota. Abrir a nota não busca o capítulo de novo.

### RNF-004 — Teclado e nomes

Botões e links têm nome acessível. O foco visível não é removido. A apresentação pode ser fechada pelo teclado (Escape).

### RNF-005 — Idioma

Interface em português do Brasil. Datas em `pt-BR`.

### RNF-006 — Falha do provedor não bloqueia a nota

Abrir, editar, visualizar e apresentar não dependem do provedor. Uma nota já criada continua com o texto embutido mesmo que o serviço da ABíbliaDigital deixe de responder. Se o provedor falhar no instante da criação, a nota ainda é gravada e a passagem afetada explica que o texto não foi capturado. Não há segunda tentativa depois.

## Tecnologias adotadas

| Camada | Escolha |
| --- | --- |
| Interface | SvelteKit 2, Svelte 5, TypeScript, Vite, Tailwind CSS |
| PWA | plugin Vite para SvelteKit (`@vite-pwa/sveltekit`) |
| Edição | CodeMirror 6 |
| Markdown renderizado | `markdown-it` |
| Tópicos e citações | funções puras no front, testadas com Vitest; o servidor consulta o provedor na criação, nas edições e ao reabrir notas com passagens pendentes, recorta o capítulo e grava o texto na nota |
| Gestos | Pointer Events |
| API | Python 3.12, FastAPI, Pydantic v2, httpx |
| Dados | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Senha | Argon2id |
| Testes de API | pytest |
| Ambiente local | Docker Compose com serviços `web`, `api` e `postgres` |
| Runtime de front no desenvolvimento | Node 22, pnpm |

Versões menores ficam nas versões estáveis atuais no momento da implementação. Não fixar uma versão antiga só para coincidir com um exemplo de blog.

## Alternativas consideradas e não adotadas

- **SvelteKit full-stack, sem API Python.** Menos processos, e foge do back em Python pedido para esta versão.
- **Next.js + FastAPI.** Atende o back em Python e pesa mais no front, sem ganho para PWA, pinça e Markdown.
- **Django com templates.** Atende Python e enfraquece apresentação, pinça e instalação como PWA.
- **SQLite.** Simples demais para várias pessoas escrevendo ao mesmo tempo no desenho alvo.
- **Editor WYSIWYG (TipTap ou similar).** A fonte Markdown e os headings são o modelo da nota e da apresentação.
- **Repositório GitHub como armazenamento.** Fora desta versão. A fonte da verdade é o PostgreSQL.
- **Outro provedor bíblico no lugar da ABíbliaDigital.** O contrato implementado é o dela. Trocar de host só por configuração, se o host novo falar o mesmo contrato. O agente não escolhe outra API nem versiona o corpus das traduções no repositório.
- **Buscar o versículo de novo ao abrir a nota.** O texto visto na gaveta é o que foi embutido na criação.

## Fora de escopo

Esta versão não inclui:

- sincronização ou exportação para GitHub
- leitura ou edição offline das notas
- compartilhamento de nota ou pasta entre pessoas
- busca global
- comentários, histórico de revisão ou lixeira
- seletor de tema claro
- exportação para PDF ou impressão formatada
- projeção em segundo ecrã
- contas por convite, papéis de igreja ou administração de usuários
- editor WYSIWYG
- citação por voz ou OCR
- atualizar ou buscar de novo o texto bíblico de uma nota já criada

## Critério de versão pronta

A versão 1 está pronta quando todos os RF e RNF acima passam e a fase 10 de [PLANO.md](PLANO.md) está concluída, incluindo a verificação manual dos fluxos de tela em viewport estreita e larga.
