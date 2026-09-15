# Bell - QA plan

> Papel: QA/Test agent (Terra). Escopo: critérios e testes para Bell - RWA Session Intelligence.
> Este plano não autoriza alterações ao motor, à UI, aos recibos nem aos dados. Data: 2026-09-13.

## 1. Objetivo e regra de aprovação

Bell só está pronto para demo quando consegue responder de forma reprodutível à pergunta
"como muda a actividade de cada wrapper quando a sessão cash fecha?", sem se transformar numa
recomendação, sem esconder dados insuficientes e sem depender de uma interpretação visual.

O QA valida cinco propriedades, por esta ordem:

1. **integridade** - cálculos usam respostas CMC e a fórmula declarada;
2. **tempo** - cada barra entra exactamente num regime, inclusive em DST;
3. **honestidade** - limites, cobertura e falhas chegam à UI e ao receipt;
4. **segurança** - não há chave CMC, dados desnecessários nem superfície de ataque evitável;
5. **uso** - o workflow e a evidência são legíveis em desktop e mobile, sem estética genérica de
   produto "AI" nem alegações inflacionadas.

### Bloqueadores de release

Não publicar/submeter se ocorrer qualquer um dos seguintes:

- uma métrica diverge entre `--offline`, receipt e página;
- uma barra é perdida, duplicada ou classificada em dois regimes;
- uma chave CMC, header de autenticação ou resposta privada entra no bundle, logs, fixture pública
  ou Git;
- o ecrã apresenta `ready` ou uma conclusão numérica quando os dados são `partial`, `stale` ou
  `insufficient-data` sem aviso inequívoco;
- a UI sugere compra, venda, arbitragem, execução, liquidez executável, qualidade de emissor,
  preço justo ou causa económica que os dados não demonstram;
- não existe caminho que permita a um juiz abrir a Evidence e reproduzir o headline a partir do
  receipt offline.

## 2. Ambientes, dados e artefactos de teste

| Camada | Fonte permitida | Propósito | Nunca fazer |
|---|---|---|---|
| Unitária | fixtures sintéticas mínimas | timezone, fórmula, validação de schema | usar rede ou chave real |
| Integração | fixtures CMC sanitizadas e versionadas | normalização, receipt, UI de evidência | editar valores brutos para "fazer passar" |
| Smoke live | chave pessoal de hackathon, server-side | confirmar contrato/endpoints/limites | expor a chave no browser ou no output |
| E2E web | receipt offline determinístico | caminho do juiz e estados de falha | depender de API live para uma demo básica |

### Convenções obrigatórias para fixtures

- Guardar `raw`, `normalized` e `expected` separadamente; incluir `endpoint`, parâmetros,
  `fetched_at`, status HTTP e `schema_version`.
- Identificar dados gravados como `fixture`, nunca como quote atual.
- Todos os timestamps devem ser ISO 8601 com offset ou `Z`; nunca datas locais ambíguas.
- Fixtures públicas não podem conter `X-CMC_PRO_API_KEY`, URL com query secreta, cookies, IPs,
  headers completos ou dados pessoais.
- Manter pelo menos: Tesla nominal; wrapper sem OHLCV; resposta `429`; resposta `5xx`; schema
  incompleto; barras duplicadas; janela DST de março e novembro.

## 3. Matriz funcional e de dados

| ID | Área / cenário | Procedimento / oracle | Esperado | Severidade |
|---|---|---|---|---|
| F-01 | Descoberta Tesla | Carregar fixture RWA com quatro wrappers e IDs | Nome, `crypto_id` e emissor exibidos; nenhum wrapper válido desaparece | P0 |
| F-02 | Exclusões transparentes | Incluir wrapper sem `crypto_id` ou inválido | Wrapper é listado como excluído com motivo; não entra no ranking/cálculo | P0 |
| F-03 | Janela default | Pedir sete dias / 168 barras horárias | Receipt declara intervalo pedido, barras recebidas, barras elegíveis e cobertura por regime | P0 |
| F-04 | Fórmula principal | Para barras controladas, calcular `(high-low)/open` | Mediana por regime coincide com valor esperado; fórmula e versão constam da Evidence | P0 |
| F-05 | Close-to-close auxiliar | Fixture com closes conhecidos | Métrica auxiliar usa apenas campos definidos e não muda o headline de range | P1 |
| F-06 | Volume horário | Fixture com `volume` rolling 24h repetido | Não soma nem mostra como volume da sessão; limitação é visível | P0 |
| F-07 | CEX/DEX mix | Quotes com `cex_volume_24h`, `dex_volume_24h`, zero e nulos | Percentagem é calculada só quando denominador é positivo; zero/nulo produz `unavailable`, não 0% inventado | P0 |
| F-08 | Snapshot coerente | OHLCV e quote obtidos em momentos diferentes | Receipt mostra `fetched_at` de cada fonte e UI avisa se exceder o limiar de frescura definido | P1 |
| F-09 | Ordenação | Wrappers com valores iguais, `null` e cobertura distinta | Ordenação estável; `null` vai para fim; cobertura nunca é escondida | P1 |
| F-10 | Contraste principal | Fixture que reproduz Tesla (Robinhood activo no weekend) | Resumo descreve observação comparativa e aponta para evidence; não atribui causa | P0 |
| F-11 | Resultado plano | Todos wrappers com métricas semelhantes | Estado/comentário diz que não há contraste claro; não força narrativa | P0 |
| F-12 | Dados insuficientes | Menos do mínimo de barras definido para um regime | `insufficient-data`; valores desse regime ficam indisponíveis e não participam na conclusão | P0 |
| F-13 | Cobertura parcial | Um wrapper falha, restantes passam | `partial`; wrappers válidos aparecem, falhado tem motivo e headline não generaliza ao activo | P0 |
| F-14 | API indisponível | `401`, `403`, `429`, timeout e `5xx` | Mensagem accionável, sem stack trace; retry apenas onde seguro; receipt preserva erro sem segredo | P0 |
| F-15 | Schema alterado | Campo CMC ausente/tipo inesperado | Falha controlada, não `0`, `NaN` ou uma conclusão falsa; alerta de contrato | P0 |
| F-16 | Duplicados/gaps | Barras repetidas, fora de ordem e horas em falta | Normalizador deduplica por chave explícita, ordena e reporta gaps; não preenche preço inventado | P0 |
| F-17 | Receipt | Executar mesma fixture duas vezes | Output equivalente (ignorando timestamps de execução declarados); inclui inputs, warnings, versão e hash se usado | P0 |
| F-18 | Offline | Desligar rede e executar receipt | Recalcula números e estado sem chave/rede; informa que é uma reprodução histórica | P0 |
| F-19 | Evidence | Abrir cada número headline | Utilizador encontra endpoint, período, timezone, barras, fórmula, warnings e timestamp em no máximo dois passos | P0 |
| F-20 | Estado UI | `ready`, `partial`, `stale`, `insufficient-data`, `api-error` | Cada estado tem rótulo, significado e próxima ação; cores não são o único sinal | P0 |

## 4. Matriz temporal: America/New_York e DST

Definição aprovada: a classificação é pelo `time_open` da barra, convertido de UTC por timezone
IANA `America/New_York`. `cash = dias úteis 09:30–16:00`; `weekday_after_hours = restante tempo
dos dias úteis`; `weekend = sábado/domingo` local. Uma barra não é repartida ao cruzar 09:30.

| ID | Caso | Entrada UTC / condição | Resultado esperado |
|---|---|---|---|
| T-01 | Cash normal | terça, 14:00Z em EST (09:00 local) | `weekday_after_hours` |
| T-02 | Limite de abertura | terça, 14:30Z em EST (09:30 local) | `cash` |
| T-03 | Dentro de cash | terça, 20:00Z em EST (15:00 local) | `cash` |
| T-04 | Limite de fecho | terça, 21:00Z em EST (16:00 local) | decidir e documentar inclusividade; teste deve reflectir essa decisão em todo o produto |
| T-05 | Pós-fecho | terça, 22:00Z em EST (17:00 local) | `weekday_after_hours` |
| T-06 | Sábado UTC/local | sábado 15:00Z | `weekend` |
| T-07 | Domingo final | domingo 23:00Z | `weekend` |
| T-08 | Segunda local | segunda 00:00 local | `weekday_after_hours`, não weekend |
| T-09 | DST começa | horas de 2026-03-08, quando 02:00 local não existe | não há offset manual; cada UTC existente é classificado uma vez e o dia não cria duplicado |
| T-10 | Primeiro cash após DST | segunda 2026-03-09 13:30Z (09:30 EDT) | `cash`; prova que a abertura deslocou uma hora em UTC |
| T-11 | DST termina | horas de 2026-11-01, quando 01:00 local se repete | duas barras distintas por UTC, ambas preservadas; nenhuma deduplicada só por hora local |
| T-12 | Primeiro cash após fim DST | segunda 2026-11-02 14:30Z (09:30 EST) | `cash` |
| T-13 | Feriado NYSE | dia útil local que seja feriado | comportamento é explicitamente `weekday_*`, a menos que calendário de feriados passe a ser fonte/versionamento do produto; não chamar "cash aberto" sem essa capacidade |
| T-14 | Timezone do browser | Browser em Lisboa, Nova Iorque e UTC | mesmos números/regimes; a apresentação pode mostrar hora local do utilizador como auxiliar, mas metodologia permanece NY |

**Invariante:** para cada barra válida, `count(cash, weekday_after_hours, weekend) = 1`. A soma das
barras classificadas mais as excluídas por validação deve igualar a contagem recebida após
deduplicação.

## 5. Website: E2E, responsividade e acessibilidade

O site deve parecer uma ferramenta de research/mercado, não um chatbot disfarçado. A referência
visual pode estudar Aster, Binance, BNB Chain e o site Dyplux, mas QA verifica comportamentos e
coerência - não copia layouts, marca ou assets de terceiros.

| ID | Check | Como testar | Critério de passagem |
|---|---|---|---|
| W-01 | Caminho de 30 segundos | Cronometrar: landing → Tesla → Run/receipt → conclusão → Evidence | juiz entende a pergunta, vê contraste e abre fonte sem criar conta |
| W-02 | Sem aparência "AI" | Revisão humana contra checklist abaixo | não há chat vazio como interface principal, avatar/"copilot", typing simulation, prompts decorativos ou promessas de inteligência sem evidência |
| W-03 | Hierarquia | Desktop 1440px e laptop 1280px | pergunta, estado dos dados, contraste e CTA Evidence precedem tabelas secundárias |
| W-04 | Mobile | 320, 375 e 390 CSS px; portrait; zoom 200% | nenhuma perda de conteúdo, scroll horizontal involuntário, controlo inacessível ou tabela sem alternativa legível |
| W-05 | Tablet/large | 768, 1024 e 1440 CSS px | grelha reorganiza sem sobreposição, truncagem de números ou CTA escondido |
| W-06 | Teclado | `Tab`, `Shift+Tab`, Enter, Space, Escape | foco visível; ordem lógica; drawers/modals prendem e devolvem foco; tudo funciona sem rato |
| W-07 | Leitor de ecrã | VoiceOver/NVDA + browser suportado | título, estado, tabela, disclosure e Evidence têm nomes/roles; alteração de estado é anunciada sem spam |
| W-08 | Semântica de tabela | Inspeção DOM + leitor de ecrã | `<caption>`, `th`, `scope` e associação row/column; números incluem unidade e contexto |
| W-09 | Cor e contraste | axe/Lighthouse + contraste manual | texto normal ≥ 4.5:1, texto grande ≥ 3:1; estado também tem texto/ícone; gráficos não dependem só da cor |
| W-10 | Movimento | `prefers-reduced-motion: reduce` | animações não essenciais param/reduzem; nenhum número muda visualmente sem alternativa |
| W-11 | Estados de carga/erro | Throttle/offline e fixtures F-12–F-15 | skeleton não imita dados; erro explica impacto e retry; layout não salta de forma disruptiva |
| W-12 | Copy e disclosures | Revisão de todas as superfícies públicas | "observed", "median range", período e limites ficam perto da conclusão; disclosure Dyplux/CMC está acessível |
| W-13 | Performance | Lighthouse em build de produção, mobile profile | sem API key, resposta raw grande ou JS não necessário no cliente; metas exactas definidas após escolher stack, regressões são bloqueadas |
| W-14 | Navegadores | última versão estável de Chrome, Safari e Firefox | fluxo crítico, downloads e tabelas operam; degradar de forma clara onde necessário |
| W-15 | Receipt link/download | Abrir e descarregar com JS desactivado quando possível | ficheiro tem MIME/nome seguro, é estável, não contém segredo e mantém provenance |

### Checklist de anti-padrões "AI"

- [ ] A página abre com a observação e a evidência, não com “Ask Bell anything”.
- [ ] Não há linguagem como “AI-powered insights”, “agentic alpha”, “magic”, “autonomous” ou
  “prediction” sem uma capacidade verificável correspondente.
- [ ] Gráficos, tabelas e estados explicam os seus cálculos; não há card com score opaco.
- [ ] O texto tem vocabulário de research: período, regime, cobertura, método, limite, receipt.
- [ ] Se no futuro existir texto gerado, é visualmente rotulado como interpretação e apenas usa
  factos já presentes no receipt.

## 6. Anti-claims e revisão editorial

| Claim/expressão proibida ou arriscada | Substituição aceitável / teste |
|---|---|
| "compre", "venda", "melhor token", "oportunidade" | remover; Bell observa comportamento, não recomenda |
| "arbitragem", "spread executável", "liquidez" | só usar se houver dados e metodologia próprios; MVP diz que range não mede profundidade nem executabilidade |
| "segue/descola da Tesla", "preço justo" | não usar: não existe preço TradFi no contrato MVP |
| "Robinhood move-se porque é DEX" | "no snapshot observado, teve X% DEX e Y% range"; causalidade é proibida |
| "mercado 24/7" como verdade geral | "este wrapper mostrou actividade no período/regime observado" |
| "seguro", "confiável", "melhor emissor" | remover; dados não avaliam direitos, solvência, custódia ou resgate |
| percentagem sem denominador/período | anexar unidade, fórmula, janela, barras e fonte |

Checks práticos:

```bash
# Procurar copy de recomendação ou causalidade antes de abrir PR/release.
rg -ni --glob '!data/fixtures/**' \
  'buy|sell|trade|alpha|arbitrage|opportunity|best|safe|guarantee|predict|because|causes?' bell

# Procurar números percentuais em copy: revisão humana confirma período e fonte.
rg -n --glob '!data/fixtures/**' '[0-9]+([.,][0-9]+)?%' bell
```

Um match não é automaticamente defeito: deve ser justificado num teste, metodologia ou citação.

## 7. Segurança e privacidade

| ID | Risco | Check de QA | Passa se |
|---|---|---|---|
| S-01 | Chave no cliente | Inspecionar bundle, DevTools Network e source maps | nenhum `CMC_API_KEY`, header pro ou endpoint autenticado aparece no browser |
| S-02 | Segredo no Git | scan local/pre-commit e revisão de fixtures/receipts | `.env` não é rastreado; só existe `.env.example` sem valor; scan limpo ou falso positivo explicado |
| S-03 | Logs | Forçar erro API e rever logs de server/CI | nunca imprime headers, bodies completos privados ou chave |
| S-04 | Input do activo | Tentar strings longas, IDs inválidos, HTML/JS e parâmetros repetidos | allowlist/validação server-side; sem SSRF, XSS, path traversal ou crash |
| S-05 | Receipt import | Abrir JSON malformado, demasiado grande e com campos inesperados | schema/version valida; erro seguro; não executa conteúdo nem substitui dados silenciosamente |
| S-06 | Rate limit/custo | Repetir Run e abrir várias tabs | cache/debounce/limite definido; 429 dá estado claro, não loop de retries |
| S-07 | Dependências | auditoria depois de escolher runtime | lockfile presente, dependências críticas auditadas e sem scripts pós-instalação inesperados |
| S-08 | Headers web | Inspecionar resposta de produção | CSP, `X-Content-Type-Options`, `Referrer-Policy` e política de frame adequadas à stack; exceções documentadas |

Comandos candidatos (adaptar ao runtime, nunca imprimir o `.env`):

```bash
# Confirmar que ficheiros de segredo não são rastreados.
git ls-files | rg '(^|/)(\.env|.*\.pem|.*\.key)$' && exit 1 || true

# Procurar padrões comuns, incluindo receipts e artefactos de build.
rg -n -i --hidden --glob '!.git/**' \
  '(X-CMC_PRO_API_KEY|CMC_API_KEY|sk-[A-Za-z0-9_-]{16,}|api[_-]?key\s*[:=])' bell

# Após existir um site Node, executar a auditoria declarada pelo projecto.
npm audit --omit=dev
```

## 8. Integração futura com CMC

| ID | Cenário | Teste | Resultado esperado |
|---|---|---|---|
| C-01 | Autenticação server-side | Smoke com segredo injectado pelo ambiente | chamada autorizada sem chave no cliente; ausência de chave dá erro de configuração seguro |
| C-02 | Quotes RWA | Validar IDs/nome/emissor contra resposta raw versionada | normalizador preserva proveniência e rejeita resposta sem campos mínimos |
| C-03 | OHLCV paginado/limitado | Janela maior que uma página ou limite de 200 | contagem/intervalo no receipt revelam truncagem; não afirma janela completa sem a ter |
| C-04 | Granularidade | Pedir `1h` e validar sequência | não aceita barras diárias/irregulares como horárias sem rótulo |
| C-05 | Plano/1005/1006 | Simular limitações do plano Startup | Bell degrada sem market pairs; explica indisponibilidade sem tentar endpoint em loop |
| C-06 | Quote sem CEX/DEX | Remover campos de volume da resposta | mix `unavailable`, nunca uma proporção estimada |
| C-07 | CMC lenta | timeout e latência elevada | timeout definido, loading honesto, cache/receipt disponíveis; sem duplicar pedidos |
| C-08 | Mudança de schema | contract test contra raw fixture e live smoke controlado | alerta falha antes de corromper cálculo; revisão manual aprova nova versão |
| C-09 | Proveniência | Abrir receipt live | endpoint, parâmetros, HTTP status, `fetched_at`, período, timezone, versão da fórmula e warnings presentes |
| C-10 | Só CMC | Inspecionar Network/dependências | nenhum fornecedor externo de dados de mercado alimenta o cálculo; fonts/analytics não podem alterar resultados |

## 9. Execução dos testes após implementação

O builder deve expor comandos reais no `bell/README.md`. Até a stack ser escolhida, usar esta
sequência como contrato; substituir apenas os placeholders pelos comandos do projecto:

```bash
# 1. Testes unitários determinísticos (motor, timezone, normalização, receipt).
<test-command> --unit

# 2. Testes de integração com fixtures, sem rede.
<test-command> --integration --offline

# 3. Reproduzir o receipt que alimenta a demo.
python3 bell.py --offline --receipt docs/proof/<receipt>.json

# 4. Validar sintaxe/estilo/tipos conforme runtime.
<lint-command>
<typecheck-command>

# 5. Levantar build de produção e correr E2E com API bloqueada.
<build-command>
<serve-command>
<e2e-command> --base-url http://127.0.0.1:<port> --offline

# 6. Só em ambiente seguro: smoke live, sem mostrar a variável no terminal.
<smoke-command> --live --asset tesla

# 7. Auditorias web depois do deploy de preview.
npx playwright test
npx @axe-core/cli http://127.0.0.1:<port>
npx lighthouse <preview-url> --only-categories=accessibility,performance,best-practices
```

### Gate de regressão mínimo em CI

- Em cada PR: lint, tipos, unitários, integração offline, testes DST, schema/receipt, scan de
  segredos e E2E do fluxo Tesla com fixture.
- Em preview: Playwright em 375px e 1440px, axe, captura de screenshot dos estados `ready`,
  `partial`, `insufficient-data` e `api-error`.
- Manual antes de submeter: smoke live com uma chave de ambiente, Safari + Chrome, teclado,
  VoiceOver, download do receipt e verificação de que a API CMC aparece na Evidence.

## 10. Critérios finais de aceitação

| Área | Critério de aprovação |
|---|---|
| Funcional | Tesla abre, encontra wrappers, calcula regimes e apresenta contraste ou recusa honesta em menos de 90 segundos |
| Reprodutibilidade | receipt offline volta a produzir os valores e warnings do caso de demo |
| Tempo | todos os testes T-01 a T-14 passam; UTC/local/DST não mudam os resultados |
| Dados | toda a métrica tem fórmula, fonte, período, barras e cobertura acessíveis na Evidence |
| Falhas | todos os estados F-12 a F-16 são demonstráveis por fixture e não produzem números falsos |
| Segurança | nenhum segredo é rastreado, servido, logado ou incluído no receipt/bundle |
| Website | fluxo crítico passa em mobile e desktop, teclado e leitor de ecrã; sem copy/opacidade que pareça um produto AI genérico |
| Claims | revisão anti-claims limpa; limites junto às conclusões; sem aconselhamento financeiro ou causalidade não suportada |
| CMC | uma chamada live verificável e o seu receipt tornam claro como a CMC foi usada e onde os limites do plano aparecem |

## 11. Registo de bugs

Cada defeito deve incluir: ID, ambiente/commit, fixture ou receipt, passos mínimos, esperado,
obtido, screenshot/console sanitizado, severidade e decisão (`fix`, `document`, `won't fix`).

Classificação: **P0** bloqueia demo/submissão; **P1** bloqueia se tocar fluxo crítico,
integridade ou acessibilidade; **P2** pode ser aceite apenas com issue explícita e sem degradar a
honestidade do produto.
