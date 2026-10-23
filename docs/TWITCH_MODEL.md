# Modelo de servidor privado da Twitch

O marco B está concluído: [modelo, correção de patrocínio e limitações](../research/twitch/model/REPORT.md). As anotações revisadas são a única fonte de rótulos; os rótulos históricos ficam apenas como proveniência.

A inferência Python está em `tools/tibia_private.py`, com parâmetros em `research/twitch/model/private-model.json`. `tools/twitch_evidence.py streams.json` retorna P(privado), seu complemento, a decisão de ocultar e as contribuições contextuais. Idioma e gameplay genérico não são evidência privada. Sem referência de servidor, a probabilidade é exatamente 1%.

Reprodução:

```sh
python3 tools/train_tibia_private.py fit       # requer NumPy
python3 tools/train_tibia_private.py evaluate  # usa o modelo congelado; não treina
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py
```

A correção de contexto foi motivada pelo teste anterior, agora declarado como regressão de desenvolvimento. Seus registros continuam fora do ajuste e da calibração; não existe teste novo intocado após a correção. Os controles de aceitação são identificados separadamente. A principal lacuna de dados são listas reais de patrocínio. A [decomposição da correção](../research/twitch/model/SPONSOR_FIX.md) documenta os pesos e a seleção agregada do limiar, incluindo o empate entre candidatos.

A integração do novo modelo na extensão e a paridade Python/JS pertencem ao marco C. Até lá, `--write-js` continua apenas reproduzindo o asset atual da extensão; não instala o modelo B. A remoção do caminho de imagem já foi aplicada ao código Python e JS. A instalação Safari não foi alterada neste marco.
