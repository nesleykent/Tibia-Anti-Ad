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
