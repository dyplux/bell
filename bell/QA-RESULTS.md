# Bell - QA results

> Verificação do protótipo e primeiro smoke test live em 2026-09-13. A chave usada no smoke test
> não está guardada no workspace.

## Estado

**Demo estática + motor offline: PASS com um bloqueio de automação.**  
**Integração CMC live: PASS no smoke test; resultado analítico: PARTIAL por dados honestamente
ausentes num wrapper.**

## Checks executados

| Check | Resultado | Evidência/comando |
|---|---|---|
| HTML servido localmente | PASS | `python3 -m http.server 8080` + `curl` ao `/` |
| Assets locais | PASS | `/styles.css`, `/snapshot.js`, `/app.js`, favicon, logo e fonte devolveram HTTP 200 |
| JavaScript | PASS | `node --check app.js` e `node --check snapshot.js` |
| Motor Bell | PASS | `python3 -m unittest discover -s bell/tests -p 'test_*.py' -v` - 19 testes + 1 live smoke opt-in |
| Property-style fuzzing | PASS | 2,000 generated OHLC bars; range invariant and finite normalisation checks |
| Receipt comparison | PASS | `bell/receipt_compare.py` compares two windows and reports flat-bar diagnostics |
| Live provenance UI | PASS | live dossier renders endpoint, status and parameters without credentials or raw bodies |
| CLI offline | PASS | `python3 bell/bell.py --offline`; receipt `bell.receipt.v1` gerado |
| Guarda live sem chave | PASS | `python3 bell/bell.py --live` recusa sem `CMC_API_KEY`, sem revelar segredo |
| Compilação Python | PASS | `python3 -m py_compile bell/engine.py bell/bell.py` |
| Receipt JSON | PASS | `jq -e '.schema_version and .wrappers and .limitations' .checks/receipt.json` |
| Receipt HTML | PASS | `.checks/receipt.html` existe e não depende de rede |
| Segredos no site | PASS | scan por `CMC_API_KEY`, `X-CMC_PRO_API_KEY`, `sk-...` e padrões de api key sem matches |
| Visual desktop | PASS provisório | `.checks/desktop.png` inspeccionado; hierarquia, tabela, contraste e disclosure presentes |
| Visual mobile | PASS provisório | `.checks/mobile-top.png` e `.checks/mobile-evidence.png` inspeccionados; layout vertical e drawer legíveis |
| Aparência não-AI | PASS provisório | sem chat principal, avatar, sparkles, gradientes, “AI-powered” ou score opaco |
| `git diff --check` | PASS | sem erros de whitespace nos ficheiros do workspace |
| Smoke CMC live | PASS | 19 chamadas HTTP 200; agrupamento Tesla, OHLCV horário e quotes latest |
| Cobertura live Bell | PASS parcial | 8/9 wrappers com 168 candles; 30 cash, 90 after-hours, 48 weekend; `TSLA.D` sem candles |
| Receipt live sanitizado | PASS | `bell/docs/proof/tesla-live-2026-09-13.json`; sem resposta bruta ou segredo |
| Reexecução offline do live | PASS | payload normalizado em `bell/docs/proof/tesla-live-2026-09-13.payload.json`; mesmos analysis fields |
| Hash dataset/receipt | PASS | receipt inclui SHA-256 canónico do payload e do resultado |
| Boundary metadata | PASS | candles que tocam 09:30/16:00 são contados; atribuição continua por `time_open` |
| Persistência multi-janela | PASS como gate | `bell/window_stability.py` bloqueia claims até quatro janelas distintas |
| Catálogo RWA completo | PASS | `bell/site/catalog.json` e `catalogue-live.js`; 7.811 activos, 79 páginas, todos HTTP 200 |
| Dossier live não-Tesla | PASS | `bell/server.py` + `GET /api/rwa?slug=gold`; 7 wrappers, 6 emissores, HTTP 200 |
| Session Review não-Tesla | PASS | Gold: 7/7 wrappers `ready`, 168 candles e 100% cash/after-hours/weekend |
| Achado comparativo | PASS inicial | Gold: weekend/cash ≈12–93% entre wrappers; Tesla snapshot ≈20–84% |

## Funcionalidades verificadas por código/artefacto

- catálogo snapshot com 7.811 activos, pesquisa por name/symbol/slug, filtros e paginação;
- selector Tesla e nove entradas do receipt, incluindo estados explícitos para dados insuficientes;
- foco de um wrapper e reset para todos;
- alternância `Hourly range` / `Relative to cash`;
- estados de venue desconhecido para Ondo e bStocks, sem converter ausência em zero;
- drawer de evidência com `dialog`, Escape, clique fora e devolução de foco;
- exportação HTML/JSON offline;
- limites junto das conclusões: range não é liquidez, venue mix não é fluxo de sessão e não há
  preço TradFi no snapshot;
- catálogo marcado como snapshot, sem chamadas API no carregamento; dossier/session são on-demand via servidor.

## Bloqueios restantes

1. O Playwright local não tem o browser Chromium instalado nesta máquina; não foi feito um E2E
   automatizado independente dos screenshots fornecidos pelo builder.
2. O website usa um receipt CMC sanitizado e um payload normalizado, não respostas CMC raw; os
   números da landing são agora recalculáveis offline a partir do payload e do hash do dataset.
3. O primeiro pedido com `time_start`/`time_end` e `interval=1h` devolveu HTTP 200 mas apenas
   seis barras por wrapper. A correção foi declarar `time_period=hourly`, `interval=hourly` e
   compensar o `time_start` exclusivo; este é um caso de fricção documentado da API.
4. O catálogo é um snapshot datado e a UI é offline por defeito. O dossier live on-demand já existe
   via `bell/server.py`; a política de freshness, cache e rate budget está em
   [`LIVE-PUBLICATION-POLICY.md`](LIVE-PUBLICATION-POLICY.md), mas o deploy final ainda é uma gate
   operacional.

## Próximo QA obrigatório

Próximo ciclo de QA:

```text
live CMC smoke → receipt sanitizado → normalizer → session engine → receipt
             → offline recomputation → same numbers/warnings → browser E2E
```

O release só passa quando os casos P0 de [`QA-PLAN.md`](QA-PLAN.md) estiverem cobertos, incluindo
missing bars, resposta 429/5xx, schema incompleto, DST, ausência de venue totals e scan de chave no
bundle. O smoke live cobre disponibilidade e shape real; ainda não substitui testes de erro HTTP
nem o E2E com Chromium instalado.
