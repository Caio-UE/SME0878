# Mineracao Estatistica e Modelagem Preditiva de Valor de Mercado no Futebol

Trabalho final da disciplina SME0829, Mineracao Estatistica de Dados, do Instituto de Ciencias
Matematicas e de Computacao da USP, primeiro semestre de 2026.

O projeto coleta, integra e analisa dados de futebol da Bundesliga para estimar o valor de mercado
dos jogadores a partir do seu desempenho em campo. A ideia central e usar estatistica e aprendizado
de maquina para tornar a precificacao de atletas mais objetiva e, com isso, apontar jogadores
subvalorizados, que rendem mais do que o preco sugere, e supervalorizados, que custam mais do que a
performance sustenta.

## Objetivo

O alvo do modelo e o valor de mercado do jogador. A tarefa e de regressao: aprender a relacao entre
as estatisticas de desempenho, a idade e a posicao de um atleta e o seu valor de mercado. O produto
final nao e apenas a previsao, mas o erro do modelo. Quando o valor previsto supera o de mercado, o
desempenho indica um ativo subvalorizado; quando fica abaixo, ha sinal de sobrepreco. Essa leitura e
o que conecta o trabalho ao seu proposito, que e reduzir a assimetria de informacao no mercado de
transferencias.

O trabalho segue o processo de Descoberta de Conhecimento em Bases de Dados, o KDD, passando por
selecao das fontes, coleta, limpeza, transformacao, mineracao e avaliacao.

## Estrutura do repositorio

    TFINAL/
      README.md                          este arquivo
      scrapers/                          codigo de coleta organizado e comentado
        sofascore/                       estatisticas de desempenho
        transfermarkt/                   valor de mercado, lesoes, transferencias, perfil
      scrap-sofascore/                   projeto original do scraper do SofaScore
      transfermarkt-scraper-main/        projeto original do scraper do Transfermarkt
      dataset_bundesliga_5seasons.csv    dataset final integrado, uma linha por jogador e temporada
      analysis.ipynb                     analise exploratoria dos dados
      modelagem_preditiva.ipynb          modelagem preditiva do valor de mercado
      data/output/                       arquivos auxiliares gerados na analise
      SlideseRelatorios/                 relatorios e slides da disciplina

A pasta scrapers e uma copia limpa e comentada dos dois scrapers, pensada para leitura e para compor
a entrega de codigo. As pastas originais foram mantidas intactas.

## Fluxo de dados

O caminho dos dados, da coleta ate os resultados, e o seguinte.

1. Coleta no SofaScore. O scraper de liga percorre cada temporada, cada time e cada jogador,
   baixando estatisticas detalhadas de desempenho como rating, gols esperados, assistencias
   esperadas, passes, dribles e desarmes.

2. Coleta no Transfermarkt. Um projeto Scrapy em camadas coleta o valor de mercado, o historico de
   transferencias, o historico de lesoes, os contratos e o perfil biografico dos jogadores, e carrega
   tudo em um banco DuckDB com esquema estrela.

3. Integracao. As duas fontes sao combinadas em um unico dataset por jogador e temporada. Um passo de
   complemento adiciona a posicao e a idade de cada atleta, obtidas do perfil do SofaScore.

4. Analise exploratoria. O notebook analysis.ipynb descreve a base, verifica a qualidade dos dados e
   levanta padroes de desempenho por posicao, temporada e faixa etaria.

5. Modelagem preditiva. O notebook modelagem_preditiva.ipynb treina e compara modelos de regressao
   para estimar o valor de mercado e usa o erro do modelo para ranquear jogadores subvalorizados e
   supervalorizados.

## Dados

O dataset final, dataset_bundesliga_5seasons.csv, cobre quatro temporadas da Bundesliga, de 22/23 a
25/26, com uma linha por jogador e temporada. Cada linha traz o valor de mercado como alvo e um
conjunto de estatisticas de desempenho, alem de posicao e idade. Sao cerca de mil e novecentas linhas
e mais de mil jogadores distintos.

O notebook de analise exploratoria usa uma base menor, com as temporadas 24/25 e 25/26, lida
diretamente do banco DuckDB do SofaScore. Essa escolha mantem a analise alinhada com a versao
apresentada no relatorio parcial.

## Como reproduzir

Recomenda-se um ambiente virtual do Python 3.12 ou superior.

Todas as dependencias estao no arquivo requirements.txt na raiz do projeto.

    python -m venv .venv
    source .venv/bin/activate      # no Windows: .venv\Scripts\activate
    pip install -r requirements.txt

Analise exploratoria e modelagem:

    jupyter notebook analysis.ipynb
    jupyter notebook modelagem_preditiva.ipynb

O notebook de modelagem le o dataset final direto do CSV e roda de ponta a ponta. O notebook de
analise le o banco do SofaScore em scrap-sofascore/db/sofascrap.duckdb e usa um cache de idades em
data/output/player_ages.csv.

Para a coleta de dados, cada scraper tem instrucoes proprias na pasta scrapers, incluindo como rodar
o scraper de liga do SofaScore e o pipeline completo do Transfermarkt. Consulte scrapers/README.md.

## Principais resultados

Da analise exploratoria:

Os dados tem alta completude, o que valida a qualidade da coleta. As metricas ofensivas, como gols e
assistencias, seguem distribuicoes bem assimetricas, com poucos jogadores concentrando a producao.
Chutes ao gol e a variavel mais correlacionada com gols. Harry Kane aparece como um ponto fora da
curva ofensivo, e atacantes como Guirassy e Undav sao os perfis estatisticamente mais proximos dele.

Da modelagem preditiva:

Os modelos explicam por volta de 84 por cento da variancia do valor de mercado em validacao cruzada
agrupada por jogador, o que evita vazamento de informacao entre treino e teste. O erro medio fica em
torno de 4,7 milhoes de euros, com desempenho melhor na faixa de valor medio e pior nos extremos. A
idade e a variavel mais determinante, seguida do clube e do rating, resultado coerente com a teoria
de valoracao de ativos, em que o ciclo de vida do atleta pesa muito no preco. A regressao linear
alcanca desempenho proximo do XGBoost, o que indica que o ganho veio das variaveis escolhidas, e nao
da complexidade do algoritmo.

## Fontes e etica

As duas fontes sao o Transfermarkt, para dados de mercado, e o SofaScore, para estatisticas de
desempenho. A coleta seguiu boas praticas de scraping educado, com pausas entre requisicoes, poucos
acessos simultaneos e respeito ao arquivo robots.txt no Transfermarkt. Os endpoints do SofaScore nao
sao oficiais e podem mudar sem aviso. Todos os dados foram usados apenas para fins academicos, no
contexto da disciplina.

## Equipe

Amanda Bezerra da Costa, Caio Uramoto Evangelista, Gustavo Negrao Ribeiro Souza, Murillo Domingos de
Almeida, Vinicio Yusuke Hayashibara e Matheus Rodrigues dos Santos.

Professor responsavel: Oilson Alberto Gonzatto Junior.
