# AMALIA-9B — q8

- model: `./amalia-mlx-8bit`
- load: 1.1s | warmup: 0.5s
- perplexity (fixed pt-PT text): **4.334**
- overall peak memory: **10.74 GB**

## cultura  (30.0 tok/s gen, 475.5 tok/s prompt, 94 tokens)
> Quem foi Luís de Camões e qual a importância d'Os Lusíadas na literatura portuguesa? Responde em três frases.

Luís de Camões foi um dos maiores poetas da língua portuguesa, autor de *Os Lusíadas*, obra-prima da literatura renascentista. A sua epopeia celebra os feitos dos portugueses durante a época dos Descobrimentos, exaltando a coragem, a ambição e o destino de Portugal. *Os Lusíadas* é fundamental na identidade cultural portuguesa, sendo considerada a obra literária mais importante do cânone nacional.

## gramatica-pt-pt  (32.3 tok/s gen, 518.4 tok/s prompt, 17 tokens)
> Reescreve a frase seguinte em português europeu formal: 'Vou estar a mandar o email pra você amanhã de manhã.' Responde apenas com a frase corrigida.

Vou enviar o e-mail para o senhor amanhã de manhã.

## resumo  (30.8 tok/s gen, 671.3 tok/s prompt, 59 tokens)
> Resume o seguinte texto numa única frase: 'A rede de metro de Lisboa foi inaugurada em 1959, sendo a primeira do país. Atualmente conta com quatro linhas — Azul, Amarela, Verde e Vermelha — que servem a capital e alguns concelhos limítrofes. Nos últimos anos, a rede tem sido alvo de projetos de expansão, incluindo a linha circular e o prolongamento até Alcântara, com o objetivo de reduzir o tráfego automóvel e as emissões na cidade.'

A rede de metro de Lisboa, inaugurada em 1959 e composta atualmente por quatro linhas, tem vindo a expandir-se com projetos como a linha circular e o prolongamento até Alcântara, visando diminuir o tráfego automóvel e as emissões na cidade.

## raciocinio  (30.3 tok/s gen, 561.3 tok/s prompt, 250 tokens)
> Um comboio parte de Lisboa às 9h15 e demora 2 horas e 50 minutos a chegar ao Porto. A que horas chega? Explica o raciocínio passo a passo.

Para descobrir a que horas o comboio chega ao Porto, precisamos de calcular o tempo total de viagem e adicioná-lo à hora de partida. Vamos fazer isto passo a passo:

### Passo 1: Converter o tempo de viagem para minutos
O comboio demora **2 horas e 50 minutos** a chegar ao Porto.

Vamos converter as 2 horas em minutos:
- 2 horas × 60 minutos/hora = **120 minutos**

Agora somamos os 50 minutos adicionais:
- 120 minutos (das 2 horas) + 50 minutos = **170 minutos**

Portanto, o tempo total de viagem é de **170 minutos**.

### Passo 2: Adicionar o tempo de viagem à hora de partida
O comboio parte de **Lisboa às 9h15**.

Vamos converter as 9h15 em minutos também:
- 9 horas = 540 minutos
- 15 minutos = 15 minutos
- Total: 540 + 1

## traducao  (31.5 tok/s gen, 539.2 tok/s prompt, 32 tokens)
> Traduz para português de Portugal: 'The meeting has been rescheduled to next Wednesday at 3 p.m. Please let me know if that works for you.' Responde apenas com a tradução.

A reunião foi reagendada para a próxima quarta-feira às 15h00. Por favor, informe-me se isso lhe convém.

## json  (30.7 tok/s gen, 516.4 tok/s prompt, 176 tokens)
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
      "regiao": "Nacional (comum no Algarve e Festas Populares)"
    }
  ]
}

## long-context needle  (1952 prompt tokens, 1190.5 tok/s prompt, needle_found=True)
azulejo
