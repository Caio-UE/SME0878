# Scrapers

Esta pasta reune o codigo de coleta de dados do projeto de Mineracao Estatistica e Modelagem
Preditiva de Valor de Ativos no Mercado de Futebol (SME0829, ICMC-USP). Todo o material analisado
no restante do trabalho, do dataset da Bundesliga ate as consultas em banco, nasce aqui.

O projeto usa duas fontes complementares, cada uma em sua subpasta:

O Transfermarkt e a fonte principal de dados de mercado. De la vem o valor de mercado dos
jogadores, o historico de transferencias, o historico de lesoes, os contratos e o perfil
biografico de cada atleta, incluindo idade, posicao, nacionalidade e pe preferido.

O SofaScore e a fonte de estatisticas de desempenho detalhadas. De la vem metricas que o
Transfermarkt nao oferece, como rating por partida, gols esperados, assistencias esperadas,
passes certos, dribles, desarmes e grandes chances criadas. Foi a base usada na analise
exploratoria e na modelagem preditiva.

A ideia e combinar as duas visoes: o desempenho em campo, medido pelo SofaScore, e o valor de
mercado e o contexto de carreira, medidos pelo Transfermarkt. O cruzamento dessas informacoes e
o que sustenta a pergunta central do projeto, que e entender o que determina o preco de um jogador.

## Organizacao da pasta

    scrapers/
      README.md                 este arquivo
      sofascore/                coleta de estatisticas de desempenho
        scrape_league.py        scraper principal, coleta uma liga inteira por temporada
        enrich_players.py       adiciona posicao e idade ao dataset final
        examples/               receitas menores baseadas no scraper
          scrape_kane.py        historico completo de um unico jogador
          scrape_bayern.py      elenco inteiro de um time em uma temporada
          filter_bundesliga.py  recorta um JSON coletado para uma competicao
        requirements.txt
      transfermarkt/            coleta de mercado, lesoes, transferencias e perfil
        tfscrap/                pacote Python com os spiders e a carga em banco
          spiders/              um spider por nivel da hierarquia de dados
          utils.py              limpeza e padronizacao do texto do site
          pipeline.py           orquestra scraping e carga em um so comando
          load.py               carrega os JSONL em um DuckDB com esquema estrela
          settings.py           configuracoes de scraping educado do Scrapy
          sql/schema.sql        definicao das tabelas do banco
        seeds/competitions.json ligas de partida do scraping
        scrapy.cfg
        requirements.txt

As pastas originais transfermarkt-scraper-main e scrap-sofascore foram mantidas intactas na raiz
do projeto. Esta pasta scrapers e uma copia organizada e comentada, pensada para leitura e para
compor a entrega de codigo.

## SofaScore

O SofaScore expoe uma API interna que nao e documentada oficialmente. Os endpoints podem mudar ou
bloquear requisicoes sem aviso. Para reduzir falhas, os scripts usam a biblioteca curl_cffi com
impersonacao de Chrome, que faz as requisicoes parecerem vir de um navegador real, e mantem uma
pausa curta entre chamadas.

O scraper principal e o scrape_league.py. Ele recebe o identificador da liga e percorre, para cada
temporada escolhida, os times, os elencos e as estatisticas de cada jogador. A saida e um unico
arquivo JSON com toda a hierarquia preservada.

    cd sofascore
    python -m venv .venv
    source .venv/bin/activate      # no Windows: .venv\Scripts\activate
    pip install -r requirements.txt

    python scrape_league.py 35                 # ultimas 5 temporadas da Bundesliga
    python scrape_league.py 35 --seasons 3     # as 3 mais recentes
    python scrape_league.py 35 --season 77333  # apenas a temporada 25/26

O enrich_players.py e um passo de complemento. Ele le o dataset final ja montado e busca, pelo
identificador de cada jogador, a posicao e a data de nascimento no perfil do SofaScore. Com a data
de nascimento, calcula a idade na abertura de cada temporada e grava as novas colunas de volta no
CSV. As respostas ficam em cache, entao o script pode ser interrompido e retomado sem refazer o
trabalho ja feito.

    python enrich_players.py                   # usa o caminho padrao do dataset

Os exemplos na pasta examples mostram usos menores da mesma API: coletar um unico jogador, um unico
time ou recortar um JSON ja coletado para uma competicao.

## Transfermarkt

O scraper do Transfermarkt e um projeto Scrapy organizado em camadas. Cada camada da hierarquia do
site tem um spider proprio, e a saida de um alimenta o proximo. A ordem e competicoes, depois clubes,
depois jogadores e, por fim, os dados de cada jogador, que sao estatisticas, lesoes, transferencias e
historico de valor de mercado.

A forma recomendada de rodar e pelo pipeline, que executa todos os spiders na ordem certa e ainda
carrega o resultado em um banco DuckDB com esquema estrela.

    cd transfermarkt
    python -m venv .venv
    source .venv/bin/activate      # no Windows: .venv\Scripts\activate
    pip install -r requirements.txt

    python -m tfscrap.pipeline                 # todas as ligas do arquivo de sementes
    python -m tfscrap.pipeline --league ES1    # apenas uma liga
    python -m tfscrap.pipeline --skip-load     # so coleta, sem carregar no banco

Tambem e possivel rodar cada spider isolado, o que ajuda a depurar. Nesse modo, a saida em JSONL de
um spider e passada como entrada do proximo.

    python -m tfscrap competitions -p seeds/competitions.json > data/competitions.jsonl
    python -m tfscrap clubs        -p data/competitions.jsonl > data/clubs.jsonl
    python -m tfscrap players      -p data/clubs.jsonl        > data/players.jsonl

O formato intermediario e o JSONL, em que cada linha e um objeto JSON independente. Ele funciona como
camada de transito entre a coleta e o banco, permitindo processar os dados aos poucos. A carga final
transforma esses arquivos em um modelo dimensional, com tabelas de fato para estatisticas, valor de
mercado, transferencias, lesoes e contrato, cercadas pelas dimensoes de jogador, clube, competicao e
tempo.

## Fluxo ate a analise

O caminho dos dados ate o restante do projeto e o seguinte. O SofaScore gera as estatisticas de
desempenho por jogador e temporada. O Transfermarkt gera o valor de mercado e o contexto de carreira.
As duas fontes sao combinadas em um unico dataset por jogador e temporada, que recebe posicao e idade
pelo enrich_players. Esse dataset final e o que alimenta o notebook de analise exploratoria e o
notebook de modelagem preditiva, onde os modelos estimam o valor de mercado e apontam jogadores
subvalorizados e supervalorizados.

## Etica e limites

A coleta seguiu boas praticas de scraping educado. No Transfermarkt, o Scrapy respeita o arquivo
robots.txt, limita o numero de requisicoes simultaneas, mantem uma pausa entre elas e ajusta o ritmo
conforme a resposta do site. No SofaScore, cujos endpoints nao sao oficiais, mantem-se uma pausa
entre chamadas e um cabecalho de navegador para reduzir bloqueios. Os dados foram usados apenas para
fins academicos, no contexto da disciplina.
