# AMALIA-9B — bf16

- model: `amalia-llm/AMALIA-9B-0626-DPO`
- load: 3.9s | warmup: 0.6s
- perplexity (fixed pt-PT text): **4.321**
- overall peak memory: **19.5 GB**

## cultura  (16.0 tok/s gen, 366.9 tok/s prompt, 122 tokens)
> Quem foi Luís de Camões e qual a importância d'Os Lusíadas na literatura portuguesa? Responde em três frases.

Luís de Camões (1524/25-1580) foi um dos maiores poetas da língua portuguesa, autor de *Os Lusíadas*, e é considerado o maior expoente da literatura portuguesa. *Os Lusíadas*, publicado em 1572, é um poema épico que celebra a viagem de Vasco da Gama à Índia, glorificando a expansão marítima portuguesa e a identidade nacional. A obra é fundamental na literatura portuguesa por consolidar a língua e a cultura, sendo um marco do Renascimento e da identidade literária de Portugal.

## gramatica-pt-pt  (17.0 tok/s gen, 399.9 tok/s prompt, 20 tokens)
> Reescreve a frase seguinte em português europeu formal: 'Vou estar a mandar o email pra você amanhã de manhã.' Responde apenas com a frase corrigida.

Vou enviar o e-mail a V. Exa. amanhã de manhã.

## resumo  (16.5 tok/s gen, 576.7 tok/s prompt, 51 tokens)
> Resume o seguinte texto numa única frase: 'A rede de metro de Lisboa foi inaugurada em 1959, sendo a primeira do país. Atualmente conta com quatro linhas — Azul, Amarela, Verde e Vermelha — que servem a capital e alguns concelhos limítrofes. Nos últimos anos, a rede tem sido alvo de projetos de expansão, incluindo a linha circular e o prolongamento até Alcântara, com o objetivo de reduzir o tráfego automóvel e as emissões na cidade.'

A rede de metro de Lisboa, inaugurada em 1959 e expandida para quatro linhas com projetos futuros como a linha circular e o prolongamento até Alcântara, visa reduzir o tráfego automóvel e as emissões na capital.

## raciocinio  (16.4 tok/s gen, 426.3 tok/s prompt, 250 tokens)
> Um comboio parte de Lisboa às 9h15 e demora 2 horas e 50 minutos a chegar ao Porto. A que horas chega? Explica o raciocínio passo a passo.

Para descobrir a que horas o comboio chega ao Porto, precisamos de calcular o tempo total de viagem e adicioná-lo à hora de partida.

**Passo 1: Converter o tempo de viagem para minutos.**

O tempo de viagem é de 2 horas e 50 minutos. Vamos converter isto para minutos:

- 2 horas = 2 × 60 = 120 minutos
- Tempo total de viagem = 120 + 50 = 170 minutos

**Passo 2: Adicionar o tempo de viagem à hora de partida.**

O comboio parte de Lisboa às 9h15. Vamos adicionar 170 minutos a esta hora.

- 170 minutos = 2 horas e 50 minutos (já sabemos isto)

Agora, vamos calcular a hora de chegada:

- 9h15 + 2 horas = 11h15
- 11h15 + 50 minutos = 12h05

**Resposta Final:**

O comboio chega

## traducao  (17.0 tok/s gen, 420.4 tok/s prompt, 33 tokens)
> Traduz para português de Portugal: 'The meeting has been rescheduled to next Wednesday at 3 p.m. Please let me know if that works for you.' Responde apenas com a tradução.

A reunião foi reagendada para a próxima quarta-feira às 15h00. Por favor, avise-me se isso lhe convém.

## json  (16.5 tok/s gen, 382.2 tok/s prompt, 173 tokens)
> Lista exatamente 5 pratos tradicionais portugueses em formato JSON: um array de objetos com os campos "nome" e "regiao". Responde apenas com o JSON.

{
  "pratos": [
    {
      "nome": "Bacalhau à Brás",
      "regiao": "Nacional"
    },
    {
      "nome": "Carne de Porco à Alentejana",
      "regiao": "Alentejo"
    },
    {
      "nome": "Arroz de Marisco",
      "regiao": "Lisboa e Vale do Tejo"
    },
    {
      "nome": "Caldo Verde",
      "regiao": "Minho"
    },
    {
      "nome": "Sardinhas Assadas",
      "regiao": "Nacional (comum em festivais de verão)"
    }
  ]
}

## long-context needle  (1953 prompt tokens, 1156.3 tok/s prompt, needle_found=True)
azulejo
