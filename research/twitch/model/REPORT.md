# Marco B: modelo treinado

**Teste reservado: 19/20 privadas detectadas; 0/5 não privadas ocultadas.** São 25 capturas reais em 23 grupos, separadas do ajuste. Limiar: P(privado) ≥98,9369%.

| Caso de aceitação | P(privado) |
| --- | ---: |
| `WAR?? KKKK \| !rubinot` | 99,70% |
| Título completo da baratuca | 2,52% |
| 35 controles sem evidência, incluindo `hunt bosses` + Português | 1,00% exato |
| Global + RubinOT, alvo misto fornecido | 50,00% |

Adicionar/remover tags de idioma e duplicar/reordenar tags não altera a probabilidade. Gameplay e comandos genéricos sozinhos ficam em 1%. Estes controles orientaram o desenvolvimento; **não são os resultados held-out**.

São 221 registros revisados, incluindo 115 reais. Divisão fixa por canal, template normalizado, parentesco e contraste: 173 treino, 23 calibração, 25 teste. Controles históricos/construídos, os alvos explícitos de base e o misto ficam no treino. Nenhuma linha foi descartada. Vocabulário de referências foi aprendido apenas nos spans afirmativos de treino, comandos/domínios e fontes citadas. Não há lista manual de servidores, pesos fixos por nome ou entrada de canal.

A representação separa referência de servidor e contexto, em vez de pontuar palavras/ngramas do título inteiro. Sem referência, P=1%; com referência, regressão logística regularizada usa relações de sessão/patrocínio/negação/comparação. Uma declaração de outra sessão só contextualiza a menção privada: não há pontuação de mundos oficiais. Nomes OT e protocolos também reconhecem projetos não catalogados. A separação entre menção e relação é motivada por [extração de relações](https://aclanthology.org/H05-1091/); as decisões contextuais vêm dos rótulos revisados.

Coeficientes condicionais mais fortes: referências reconhecidas +16,98; coordenação da referência +6,73; comando de servidor +5,94. Atenuam: referência histórica −13,62; patrocínio explícito −10,25; posição tardia −9,31. São coeficientes correlacionados de contexto, não probabilidades nem pesos de nomes. [Todos os pesos e explicações por teste](results.json).

Calibração por [temperatura](https://proceedings.mlr.press/v70/guo17a.html), ajustada só na partição de calibração, sob os contratos de base/50%. Brier held-out **0,0381**, log-loss **0,1510**, ECE em 4 faixas **0,0391**. Ridge escolhido pelos controles de treino; limiar escolhido pela calibração. O teste foi aberto depois de congelar os parâmetros e não gerou reajuste.

**Limitação concreta:** o negativo de patrocínio `audit:42` recebeu **97,52% privado**, ficando visível apenas pelo limiar conservador. Há somente 2 listas reais confirmadas de patrocínios, além de 2 outros negativos reais de promoção incidental. Com 5 negativos no teste e dados selecionados de um único dia, não há prova de calibração em produção ou de risco quase zero. Novos exemplos do diagnóstico são necessários; não bloquearam este marco.

[Modelo](private-model.json), [reprodução](../../../tools/train_tibia_private.py) (`fit` requer NumPy; `evaluate` não refaz o ajuste). A fixture antiga virou índice para as anotações; rótulos antigos e o pipeline de imagem foram retirados dos testes. Verificações do projeto passaram. Integração/paridade JS e instalação Safari ficam para C; nenhum navegador foi atualizado neste marco.
