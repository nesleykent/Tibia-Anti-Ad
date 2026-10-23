# Lacuna de dados antes do marco B

**Não há dados suficientes para aprender sessão vs promoção com segurança.** Há 115 registros reais de metadados no pacote, mas apenas **4 negativos reais confirmados de promoção incidental durante sessão original**: baratuca, audit:42, audit:179 e audit:218. Os dois primeiros são listas de patrocínios; os dois novos acrescentam menções incidentais de idle/OT em declarações de sessão. Os outros negativos não substituem esse contraste.

Contagens da versão atual de [annotation-proposals.json](annotation-proposals.json), por contexto proposto da menção selecionada. “Real” significa captura de metadados ou exemplo de stream real informado pela mantenedora. Não significa sessão verificada independentemente. Os 65 testes históricos, 7 exemplos de requisitos, 18 construções e 16 contrafactuais de idioma ficam fora destas contagens.

| Contexto | Registros reais | Inputs distintos (título + tags) | Canais identificados distintos | Alvos: privada / não privada / ausente |
| --- | ---: | ---: | ---: | --- |
| Sessão | 87 | 87 | 83 | 69 / 18 / 0 |
| Promoção | 17 | 17 | 14 | 13 / 4 / 0 |
| Sem evidência | 8 | 8 | 8 | 1 / 0 / 7 |
| Contexto não resolvido | 1 | 1 | 1 | 0 / 0 / 1 |
| Comparação | 1 | 1 | 1 | 0 / 1 / 0 |
| Negação | 0 | 0 | 0 | 0 / 0 / 0 |
| Sessões mistas | 1 | 1 | 1 | alvo fracionário 0,5 |
| Total | 115 | 115 | 107 | 83 / 23 / 8, mais 1 misto |

Canais são deduplicados globalmente no total, não somados entre contextos. O exemplo informado por você não tem canal fornecido e não entra na contagem de canais. Identidades servem exclusivamente para proveniência e separação dos conjuntos, nunca como preditores. Inputs distintos não garantem observações independentes: títulos variam entre capturas e templates podem se repetir.

Dos 17 registros reais de promoção, **13 são propostas positivas de apresentação principal/abertura de servidor privado**. Apenas 4 são promoção incidental em sessões originais, adjudicadas por você (`maintainer-example:0`, `audit:42`, `audit:179`, `audit:218`). Os novos casos não substituem a necessidade de listas variadas de patrocinadores. O único comparativo real (`live2115:460`) é personagem contra monstros. Não há negações naturais nesta amostra. O título misto (`audit:384`) recebe alvo 0,5 por sua decisão explícita de que declara ambas as sessões; não é calibração observada de frequência. A rodada 3 resolve todas as decisões solicitadas neste pacote, incluindo as tags privadas e o escopo de Project Zomboid.

Não seria honesto ajustar o contexto agora e alegar que aprendeu essa distinção. Com esses dados, um modelo pode apenas associar nomes/comandos à classe majoritária e repetir a falha. Construções ajudam a especificar o comportamento e verificar invariâncias, mas não demonstram generalização natural. Os alvos históricos ausentes permanecem ausentes por proveniência. Conforme a instrução mais recente da mantenedora, esses inputs recebem supervisão explícita de ausência de evidência privada e previsão obrigatória de 1%; não podem ser descartados nem entrar como positivos. Isso é uma restrição de comportamento do modelo, não uma alegação de verificação independente da sessão.

# Coleta proposta antes do treinamento

1. Capturar uma amostra natural da categoria Tibia em pelo menos 3 dias e horários diferentes, preservando título integral, todas as tags, horário, referência pública e identificador de captura. Aproveitar os metadados da página usados em `extension/src/tibia-props.js`, validando completude; o coletor antigo deixou tags indisponíveis e incluiu prompts de acessibilidade. Rejeitar entradas truncadas/prompts.
2. Separadamente, enriquecer os candidatos de treino com **50 negativos reais verificados de listas de patrocínios**, idealmente de pelo menos 30 canais, e pelo menos 50 positivos reais de comandos que identificam a sessão. Incluir o mesmo identificador privado em ambos os contextos, variedade de comerciantes/patrocinadores e listas com quantidades diferentes de comandos. Não selecionar por idioma. Estes números são metas iniciais de coleta, não garantia de suficiência.
3. Confirmar o servidor efetivamente jogado por evidência pública independente e contemporânea: declaração explícita sobre a sessão, referência verificável ao servidor/personagem ou observação humana do jogo ao vivo. Registrar fonte, horário, justificativa e responsável pela confirmação, sem arquivar imagens. Não inferir o alvo de nível, vocação, aparência “oficial”, quantidade de comandos ou identidade do canal. Se não houver prova, manter o alvo histórico ausente e registrar supervisão de ausência de evidência privada, com expectativa de 1%, sem descartar o input. Não contatar streamers sem autorização.
4. Buscar também negações e comparações naturais; registrar separadamente se a menção é sessão, patrocínio incidental, apresentação principal de um lançamento, negação ou comparação. Preservar múltiplas menções e seu escopo. Os alvos atuais são por menção e por stream, não uma simples etiqueta para toda ocorrência de `!rubinot`.
5. Voltar ao marco A com os novos exemplos e sua proveniência para revisão. Só depois congelar treino, calibração e teste por grupos de canal/transmissão/template, reservando também datas posteriores e servidores não vistos. Canais são chaves de separação, nunca features. Não ajustar thresholds no teste final.

A amostra enriquecida não estima a prevalência real e não serve sozinha para comprovar calibração em produção. Reservar amostra natural rotulada para calibração e teste, mantendo-a fora do ajuste e com composição declarada. Se não houver negativos suficientes, relatar essa limitação antes de avançar ao marco B.

Para dimensionar a evidência de segurança: com 0 falsos ocultamentos em 300 exemplos oficiais **independentes** de teste, o limite superior binomial unilateral de 95% ainda é aproximadamente 1% (`1 - 0.05^(1/300)`). Isso é um cálculo de planejamento, não um resultado obtido. Repetições do mesmo canal/template não contam como 300 observações independentes. Os 50 negativos propostos para coleta de treino não fazem parte desse teste.

Nenhuma coleta adicional, treinamento ou alteração da extensão foi executada nesta revisão. A revisão deste pacote foi concluída pela mantenedora. A próxima ação do agente é fechar a coleta dos negativos que faltam e apresentar apenas as novas anotações antes do marco B.
