# Regras permanentes do projeto Verso

## Versionamento semântico

Quando o usuário pedir uma versão, um release, uma tag ou "bump", siga SemVer `MAJOR.MINOR.PATCH` (`vMAJOR.MINOR.PATCH`) e aplique a regra abaixo antes de modificar arquivos:

- **MAJOR**: incremento de `X` para incompatibilidade deliberada: quebra de API pública, formato persistido/migração incompatível, mudança que exige ação manual de usuário ou remoção de funcionalidade pública.
- **MINOR**: incremento de `Y` para funcionalidade nova compatível; também inclusão significativa de capacidades PWA, endpoints adicionais ou comportamento novo que não quebra o uso existente.
- **PATCH**: incremento de `Z` para correção de bug, ajuste de segurança sem quebra, melhoria interna, desempenho ou correção de documentação diretamente ligada ao comportamento já publicado.

Exemplos:

- Login ou autorização quebrado e corrigido: `PATCH`.
- Convites com uma nova opção opcional e fluxo compatível: `MINOR`.
- Mudar o formato do banco ou a estrutura de uma resposta existente sem compatibilidade: `MAJOR`.

Para mudanças sem informação suficiente, solicite de forma breve qual das três classes se aplica; não invente uma versão.

### Como aplicar uma versão

1. O número deve ser único para todo o produto Verso.
2. Versione a API e o frontend separadamente, conforme a aplicação alterada.
3. Atualize apenas o manifesto correspondente:
   - API: `apps/api/pyproject.toml`, campo `version`;
   - frontend: `apps/web/package.json`, campo `version`.
   - Se ambas forem alteradas, atualize os dois para os números correspondentes a cada aplicação.
4. Não altere dependências ou o manifesto PWA apenas para forçar uma versão.
5. Execute testes relevantes e confirme o build antes de gerar a tag.
6. Para releases estáveis, crie tag Git com prefixo `v`, por exemplo `v1.2.3`.
7. Antes de criar uma tag, garanta que o diretório esteja sem mudanças não relacionadas pendentes e que o branch esteja preparado pelo usuário.
8. Nunca publique credenciais, senhas, URLs privadas ou dados reais de implantação em arquivos versionados.

### Pré-releases

Use somente quando solicitado: `vMAJOR.MINOR.PATCH-alpha.1`, `-beta.1` ou `-rc.1`. Pré-releases não usam a tag `latest` como release estável.

### Commits e Docker

O workflow produz imagens Docker separadas `verso-api` e `verso-web`. Uma tag Git publica apenas as imagens cujos manifests tiverem a mesma versão da tag. Não crie uma nova versão somente por mudar arquivos de infraestrutura; use PATCH se o produto publicado e o comportamento externo não mudarem, ou MAJOR/MINOR se a implantação introduzir mudança incompatível ou funcional.
