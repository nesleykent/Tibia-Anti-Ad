# Marco B: modelo corrigido

**A lista real de patrocínios que recebia 97,52% privado agora recebe 1,00%.** A [decomposição completa](SPONSOR_FIX.md) mostra a falha, os pesos anteriores e novos e a correção dos aliases. Não houve alteração de rótulos.

| Aceitação | P(privado) |
| --- | ---: |
| `WAR?? KKKK \| !rubinot` | 99,99997% |
| Título completo baratuca | 1,00% |
| Lista real `audit:42`, com `50tc/mês` | 1,00% |
| 35 controles sem evidência, incluindo `hunt bosses` + Português | 1,00% exato |
| Global + RubinOT, alvo misto fornecido | 50,00% |

Idioma, ordem/duplicação de tags, preenchimento com gameplay e comandos genéricos não alteram esses resultados. A lista real virou caso de aceitação, permanecendo fora do ajuste e da calibração.

São 221 registros revisados, 115 reais: **173 treino, 23 calibração, 25 regressão de desenvolvimento**. Os 25 eram o teste anterior; como sua falha orientou a engenharia de features, **não há teste novo intocado após esta correção**. Na regressão: 20/20 privadas detectadas e 0/5 não privadas sinalizadas; Brier 0,0000201, log-loss 0,0021643, ECE 0,0021542. São medidas de desenvolvimento, sem garantia de calibração em produção. Nenhum registro foi descartado ou transferido para o ajuste; grupos de canal, template, parentesco e contraste continuam separados.

O modelo usa regressão logística regularizada sobre referências privadas e suas relações contextuais. Sem referência, P=1%. Com referência, os pesos aprendidos modulam sessão, promoção, negação e comparação. Não pontua idioma, gameplay ou mundos oficiais. Vocabulário/aliases vêm somente de spans afirmativos de treino e fontes citadas. A separação referência/relação é motivada por [extração de relações](https://aclanthology.org/H05-1091/); a [temperatura](https://proceedings.mlr.press/v70/guo17a.html) é ajustada na calibração separada. O piso e a restrição dos exemplos mistos são contratos explícitos fornecidos pelo mantenedor.

Principais coeficientes positivos: coordenação de referência +7,5701; identificação privada +5,0833; comando de servidor +4,7776; comparação +2,9782. Principais atenuantes contextuais: declaração de outra sessão −12,6534; oferta comercial −9,2041; par de nomes concorrente −8,8697; referência histórica −7,6748; patrocínio −7,4538. São pesos correlacionados, não probabilidades. O par concorrente reconhece uma estrutura de título, sem lista de mundos oficiais. `ot_name` agora é não negativo e ficou em 0; posição, quantidade de referências e contagem/proporção de comandos foram removidas.

**Limiar: 99%.** Uma grade fixa minimiza o custo agregado por grupo de calibração, com custo de falso ocultamento 50 e de privada perdida 1. Todos os pontos empataram (16/18 privadas, 0/5 não privadas); 99% resulta do desempate conservador pelo corte de custo 50/51. A razão 50:1 é política assumida, não estimativa dos dados. O limiar não foi colocado acima de um exemplo específico e não resolve a classificação por si: os títulos de patrocínio já ficam em 1%.

A lacuna continua: apenas 2 listas reais confirmadas de patrocínios, além de 2 outros negativos reais de promoção incidental. Futuras capturas do diagnóstico servirão para ampliar esses contextos e avaliar generalização. Isso não bloqueia este marco.

[Modelo](private-model.json), [resultados e explicações](results.json), [reprodução](../../../tools/train_tibia_private.py). Inferência Python sem imagens. Integração/paridade JS e instalação Safari ficam para C.
