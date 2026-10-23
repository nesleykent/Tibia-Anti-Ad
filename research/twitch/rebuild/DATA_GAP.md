# Lacuna de dados antes do marco B

**Não há dados suficientes para aprender sessão vs promoção com segurança.** Há 115 registros reais de metadados no pacote, mas apenas **2 negativos reais confirmados de stream original com lista de patrocínios**: o título da baratuca e audit:42, agora adjudicado por você. Os outros negativos não substituem esse contraste.

Contagens da versão atual de [annotation-proposals.json](annotation-proposals.json), por contexto proposto da menção selecionada. “Real” significa captura de metadados ou exemplo de stream real informado pela mantenedora. Não significa sessão verificada independentemente. Os 65 testes históricos, 7 exemplos de requisitos, 18 construções e 16 contrafactuais de idioma ficam fora destas contagens.

| Contexto | Registros reais | Inputs distintos (título + tags) | Canais identificados distintos | Alvos: privada / não privada / ausente |
| --- | ---: | ---: | ---: | --- |
| Sessão | 83 | 83 | 79 | 65 / 18 / 0 |
| Promoção | 15 | 15 | 12 | 13 / 2 / 0 |
| Sem evidência | 8 | 8 | 8 | 1 / 0 / 7 |
| Contexto não resolvido | 8 | 8 | 8 | 0 / 0 / 8 |
| Comparação | 1 | 1 | 1 | 0 / 1 / 0 |
| Negação | 0 | 0 | 0 | 0 / 0 / 0 |
| Total | 115 | 115 | 107 | 79 / 21 / 15 |

Canais são deduplicados globalmente no total, não somados entre contextos. O exemplo informado por você não tem canal fornecido e não entra na contagem de canais. Identidades servem exclusivamente para proveniência e separação dos conjuntos, nunca como preditores. Inputs distintos não garantem observações independentes: títulos variam entre capturas e templates podem se repetir.

Dos 15 registros reais de promoção, **13 são propostas positivas de apresentação principal/abertura de servidor privado**. Apenas 2 são promoção incidental durante sessão original, confirmados por você (`maintainer-example:0` e `audit:42`). Portanto, o volume aparente de “promoção” não fornece 15 negativos de patrocínio. O único comparativo real (`live2115:460`) é personagem contra monstros, não comparação entre servidores. Não há negações naturais nesta amostra. A rodada 2 incorpora as adjudicações individuais e aprovações em lote da mantenedora. Aprovar o restante das identidades privadas não cria novos negativos de patrocínio.

Não seria honesto ajustar o contexto agora e alegar que aprendeu essa distinção. Com esses dados, um modelo pode apenas associar nomes/comandos à classe majoritária e repetir a falha. Construções ajudam a especificar o comportamento e verificar invariâncias, mas não demonstram generalização natural. Os alvos históricos ausentes permanecem ausentes por proveniência. Conforme a instrução mais recente da mantenedora, esses inputs recebem supervisão explícita de ausência de evidência privada e previsão obrigatória de 1%; não podem ser descartados nem entrar como positivos. Isso é uma restrição de comportamento do modelo, não uma alegação de verificação independente da sessão.

# Coleta proposta antes do treinamento

1. Capturar uma amostra natural da categoria Tibia em pelo menos 3 dias e horários diferentes, preservando título integral, todas as tags, horário, referência pública e identificador de captura. Aproveitar os metadados da página usados em `extension/src/tibia-props.js`, validando completude; o coletor antigo deixou tags indisponíveis e incluiu prompts de acessibilidade. Rejeitar entradas truncadas/prompts.
2. Separadamente, enriquecer os candidatos de treino com **50 negativos reais verificados de listas de patrocínios**, idealmente de pelo menos 30 canais, e pelo menos 50 positivos reais de comandos que identificam a sessão. Incluir o mesmo identificador privado em ambos os contextos, variedade de comerciantes/patrocinadores e listas com quantidades diferentes de comandos. Não selecionar por idioma. Estes números são metas iniciais de coleta, não garantia de suficiência.
3. Confirmar o servidor efetivamente jogado por evidência pública independente e contemporânea: declaração explícita sobre a sessão, referência verificável ao servidor/personagem ou observação humana do jogo ao vivo. Registrar fonte, horário, justificativa e responsável pela confirmação, sem arquivar imagens. Não inferir o alvo de nível, vocação, aparência “oficial”, quantidade de comandos ou identidade do canal. Se não houver prova, manter o alvo histórico ausente e registrar supervisão de ausência de evidência privada, com expectativa de 1%, sem descartar o input. Não contatar streamers sem autorização.
4. Buscar também negações e comparações naturais; registrar separadamente se a menção é sessão, patrocínio incidental, apresentação principal de um lançamento, negação ou comparação. Preservar múltiplas menções e seu escopo. Os alvos atuais são por menção e por stream, não uma simples etiqueta para toda ocorrência de `!rubinot`.
5. Voltar ao marco A com os novos exemplos e sua proveniência para revisão. Só depois congelar treino, calibração e teste por grupos de canal/transmissão/template, reservando também datas posteriores e servidores não vistos. Canais são chaves de separação, nunca features. Não ajustar thresholds no teste final.

A amostra enriquecida não estima a prevalência real e não serve sozinha para comprovar calibração em produção. Reservar amostra natural rotulada para calibração e teste, mantendo-a fora do ajuste e com composição declarada. Se não houver negativos suficientes, relatar essa limitação antes de avançar ao marco B.

Para dimensionar a evidência de segurança: com 0 falsos ocultamentos em 300 exemplos oficiais **independentes** de teste, o limite superior binomial unilateral de 95% ainda é aproximadamente 1% (`1 - 0.05^(1/300)`). Isso é um cálculo de planejamento, não um resultado obtido. Repetições do mesmo canal/template não contam como 300 observações independentes. Os 50 negativos propostos para coleta de treino não fazem parte desse teste.

Nenhuma coleta adicional, treinamento ou alteração da extensão foi executada nesta revisão. A próxima ação é revisar a [fila compacta](REVIEW.md) e fechar a coleta dos negativos que faltam antes do marco B.
