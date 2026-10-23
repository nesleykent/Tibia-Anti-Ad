# Correção do contexto de patrocínio

Fonte: `audit:42`, [canal radizao](https://www.twitch.tv/radizao).

✋🤪🤚 - EK 2450 -❗!loja❗😱50tc/mês😱⚠️não reseta⚠️ !rubinot - !neo !exitlag

Tags: Tibia, Inglês, TDAH, twinkmaldito.

**P(privado): 97,52085% antes; 1,00% agora. Complemento exibido: 99,00%.** O caso continua fora do ajuste e da calibração; virou controle de desenvolvimento porque motivou esta correção.

## Decomposição anterior

Cada contribuição é valor × coeficiente em log-odds, antes da temperatura. Não são pontos percentuais somáveis. Logit total: 3,67085181; temperatura multiplicativa: 1,00035352; sigmoide: 97,52085%.

| Feature | Valor | Coeficiente | Contribuição |
| --- | ---: | ---: | ---: |
| `identified_reference` | 1.000000 | +1.555477 | +1.555477 |
| `title_reference` | 1.000000 | -0.136108 | -0.136108 |
| `tag_reference` | 0.000000 | -2.682671 | -0.000000 |
| `server_command` | 1.000000 | +5.937931 | +5.937931 |
| `server_domain` | 0.000000 | +0.781795 | +0.000000 |
| `ot_name` | 1.000000 | -1.401663 | -1.401663 |
| `protocol` | 0.000000 | +2.831599 | +0.000000 |
| `launch_context` | 0.000000 | +2.222214 | +0.000000 |
| `other_commands` | 0.500000 | +0.943411 | +0.471705 |
| `command_share` | 0.250000 | +0.387246 | +0.096812 |
| `late_reference` | 0.666667 | -9.309842 | -6.206562 |
| `negated_reference` | 0.000000 | -3.652083 | -0.000000 |
| `comparison` | 0.000000 | +1.877753 | +0.000000 |
| `past_reference` | 0.000000 | -13.622014 | -0.000000 |
| `sponsor_context` | 0.000000 | -10.253737 | -0.000000 |
| `commercial_context` | 1.000000 | -2.305597 | -2.305597 |
| `bracketed_reference` | 0.000000 | +2.556061 | +0.000000 |
| `multiple_references` | 0.333333 | +16.976568 | +5.658856 |
| `current_session_relation` | 0.000000 | -3.428172 | -0.000000 |
| `coordinated_reference` | 0.000000 | +6.726338 | +0.000000 |
| `commercial_offer` | 0.000000 | -5.050635 | -0.000000 |
| `separate_session_declaration` | 0.000000 | -8.328389 | -0.000000 |

A expressão de preço exigia uma fronteira de palavra antes de `tc`: reconhecia `50 tc/mês`, mas perdia `50tc/mês`. Por isso `commercial_offer` ficou zerada. Além disso, reconhecimentos sobrepostos geravam crédito por quantidade (`multiple_references`), e a posição relativa mudava com texto neutro (`late_reference`). A soma desses atalhos venceu o contexto comercial. O limiar antigo só escondia o erro de probabilidade.

## Correção e novos pesos

- `ot_name` tinha peso negativo, −1,401663. Agora a família de pistas de identificação tem restrição não negativa; o ajuste deu **0,000000** a `ot_name`. O nome continua ativando a referência reconhecida, +5,083303.
- `late_reference` e `multiple_references` foram removidas. Também saíram os bônus de campo, quantidade e proporção de comandos. Preencher o título com gameplay, repetir um nome ou acrescentar comandos genéricos não cria peso.
- Aliases são extraídos de spans afirmativos do treino e fontes citadas. Saíram `httpspokehero`, `otponlinecom`, `idleworld` e `rubintoinfernum`; entram a marca inteira `pokeidleworld` e a variante anotada `rubinto`. Não há tabela manual de nomes ou peso por canal.
- `50tc/mês`, `50 tc/mês` e `50 TC / mês` produzem o mesmo contexto. O preço não determina a classe: ativa uma relação comercial cujo coeficiente é aprendido nos rótulos existentes.

| Feature ativa neste título | Valor | Novo coeficiente | Contribuição |
| --- | ---: | ---: | ---: |
| `identified_reference` | 1 | +5.083303 | +5.083303 |
| `server_command` | 1 | +4.777568 | +4.777568 |
| `ot_name` | 1 | +0.000000 | +0.000000 |
| `commercial_context` | 1 | -3.688298 | -3.688298 |
| `commercial_offer` | 1 | -9.204125 | -9.204125 |

As demais features contribuem 0. Logit: −3,03155236; escala de temperatura: 1,51746293. Após sigmoide e piso de 1%, P(privado)=1%. A mesma representação dá 1% ao título baratuca e 99,99997% a `WAR?? KKKK | !rubinot`. Os coeficientes foram reajustados nos mesmos 173 exemplos de treino, com calibração nos mesmos 23 exemplos separados.

## Limiar e alcance da avaliação

Selecionado **99%** numa grade fixa de 50%, 60%, 70%, 80%, 90%, 95%, 97,5%, 99%, 99,5%, 99,9%, minimizando custo médio por grupo nos 23 grupos de calibração. Política explícita: falso ocultamento custa 50 vezes uma privada perdida; essa razão é uma escolha conservadora, não uma quantidade estimada dos dados.

Todos os pontos da grade empataram: 16/18 privadas detectadas e 0/5 não privadas sinalizadas. Os dados, portanto, não identificam um limiar único. O desempate usa o ponto da grade imediatamente acima do corte de custo 50/51=98,0392%, resultando em 99%. Não se usa a probabilidade máxima de uma live negativa nem ajuste imediatamente acima dela. O título corrigido permanece visível mesmo com limiar de 5%.

O teste anterior foi usado para identificar a falha e agora é regressão de desenvolvimento: 20/20 privadas detectadas, 0/5 não privadas sinalizadas. Não existe teste novo intocado após a correção. Esses números não são evidência independente de generalização. Há somente 2 listas reais confirmadas de patrocínio e 2 outros negativos reais de promoção incidental; a lacuna será suprida com futuros exports do diagnóstico.

[Dados completos da decomposição e grade](sponsor-correction.json). [Modelo e resultados](REPORT.md).
