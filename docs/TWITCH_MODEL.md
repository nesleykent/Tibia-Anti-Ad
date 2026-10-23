# Modelo de servidor privado da Twitch

Os marcos B e C usam o mesmo modelo congelado: [modelo, correção de patrocínio e limitações](../research/twitch/model/REPORT.md). As anotações revisadas são a única fonte de rótulos; os rótulos históricos ficam apenas como proveniência.

A inferência Python está em `tools/tibia_private.py`, com parâmetros em `research/twitch/model/private-model.json`. `tools/twitch_evidence.py streams.json` retorna P(privado), seu complemento, a decisão de ocultar e as contribuições contextuais. Idioma e gameplay genérico não são evidência privada. Sem referência de servidor, a probabilidade é exatamente 1%.

Reprodução:

```sh
python3 tools/train_tibia_private.py fit       # requer NumPy
python3 tools/train_tibia_private.py evaluate  # usa o modelo congelado; não treina
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py
```

A correção de contexto foi motivada pelo teste anterior, agora declarado como regressão de desenvolvimento. Seus registros continuam fora do ajuste e da calibração; não existe teste novo intocado após a correção. Os controles de aceitação são identificados separadamente. A principal lacuna de dados são listas reais de patrocínio. A [decomposição da correção](../research/twitch/model/SPONSOR_FIX.md) documenta os pesos e a seleção agregada do limiar, incluindo o empate entre candidatos.

O marco C integra o modelo na extensão. `--write-js` exporta pesos, aliases, calibração, limiar, expressões de reconhecimento e normalização da fonte Python para `filters/sources/twitch/tibia-evidence.json` e gera `extension/src/tibia-evidence.js`. O hash do modelo congelado acompanha os diagnósticos. Revisão 4 rejeita caches incompatíveis. O navegador retorna P(privado), complemento, decisão de ocultar e contribuições, sem estado indeterminado. O Safari exibe somente o complemento numérico; a descrição acessível identifica `1 − P(private server)`.

Paridade: os 221 exemplos revisados e controles adicionais de Unicode/contexto têm as mesmas referências, features, contribuições, logit e decisão. Probabilidades concordam a 15 casas decimais, tolerando apenas arredondamento da função exponencial entre runtimes. O somatório compensado é explícito nas duas linguagens para funcionar também em versões antigas de Python.

O teste offline de navegador verifica transporte de metadados completos, ocultação, complemento, desativação do filtro e layout em 1280 e 375 pixels. A atualização pessoal Safari verifica assinatura e registro, separadamente da ativação no navegador e da persistência após reinício.

`tests/browser/capture-tibia.cjs` faz uma única navegação à categoria ao vivo com a extensão real em perfil Chrome isolado, percorrendo a lista e preservando a primeira observação de cada canal. Recusa sobrescrever a captura e mantém os metadados no diretório ignorado `local/`. O diagnóstico registra ocultação efetiva, probabilidade e explicações. Não chama treinamento nem atribui rótulos. Ver [registro do marco C](../research/twitch/model/MILESTONE_C.md).

## Directory controls and diagnostics (1.6.3)

Both browsers offer Show, Move to bottom and Hide. The slider is the minimum
displayed complement, `1 - P(private server)`, from 0% to 100%. Streams below it
are affected; streams equal to or above it stay in the first group. The default
is 1%, corresponding to the frozen model's conservative 99% private-server
policy. Show keeps Twitch order and reports zero affected streams. Move to bottom
counts the affected streams without hiding them; Hide counts hidden streams.
Per-broadcast Show overrides apply in both modes.

Move to bottom sets CSS order on Twitch's existing flex/grid cells. It preserves
Twitch order inside each group. When the list has been scrolled, the visual prefix
through the visible row stays in place and only the remaining suffix is regrouped
when new cards load. Changing the mode, threshold or a Show override explicitly
regroups the complete loaded list, including the visited prefix. During automatic
loads, a newly loaded preferred stream does not jump ahead of streams already
reached by the reader. No React-owned node is moved. Keyboard
and assistive navigation retain Twitch's DOM order.

Export JSON in the Diagnostics section saves a local JSON object. Its header
contains `captured_at` (UTC ISO 8601), `url`, `extension_version`, `model_revision`,
`model_sha256`, `threshold`, `threshold_metric`, `mode` and `enabled` (whether
filtering is active). `streams` contains the existing capture fields `channel`,
`title`, `tags` and `viewers` (null when unavailable), plus:

- `private_probability`, `display_probability`, `displayed_percentage` (0 to 100),
  `displayed_text` (the shared localized formatting) and `percentage_shown`
  (Safari's existing probability badge is separate from Chrome's presentation).
- `references`, `contributions` with feature, value, weight and raw-logit
  contribution, and `raw_logit`. Calibration parameters belong to the model
  identified by the hash.
- `hide` (below the active threshold), `affected` (after mode and Show overrides),
  `hidden` (actually hidden by this filter) and `present_on_page`.

Titles and tag arrays retain the text, ordering and duplicates read from Twitch,
without truncation or inference normalization. Viewer counts come from the card’s
`currentViewerCount` integer, not rounded display strings such as `3.7K`. They
refresh as Twitch updates its card data. Each channel retains its most
recently evaluated metadata in page memory, including after Twitch unmounts its
card. Leaving the category or reloading clears this session. Removed cards retain
their last evaluated state; `present_on_page` distinguishes them. A model or
settings change recalculates retained results with the exported header's policy.
Exports are user-initiated and are not uploaded or stored in extension storage.

Both the evaluation CLI (`python3 tools/twitch_evidence.py capture.json`) and
annotation source loading accept this envelope as well as historical bare arrays.
The download is initiated inside the Twitch page, using a JSON Blob and an anchor
with `download`, without the extension downloads API. The native Safari popover
requests that same operation through its existing native settings bridge and
reports success or errors from the active tab. A download request alone does not
prove that Safari saved the file; browser verification is recorded separately.
