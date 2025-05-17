# Detetive de Preços e Disponibilidade Relâmpago 🕵️💰📍

Este projeto em Python utiliza o Google Generative AI SDK (Gemini) e o Google Agent Development Kit (ADK) para criar um sistema inteligente com múltiplos agentes de IA. O objetivo é ajudar usuários a encontrar informações sobre preços e disponibilidade de produtos, tanto em lojas físicas próximas quanto online, de forma rápida e eficiente.

## O projeto pode ser encontrado em 2 formas
1. Pronto para o colab arquivo [Projeto Colab](https://github.com/ricardomouro/colab-first-steps/blob/main/Detetive_Pre%C3%A7os_Disponibilidade_Rel%C3%A2mpago.ipynb)
2. Em {Python](https://github.com/ricardomouro/colab-first-steps/blob/main/detetive_pre%C3%A7os_disponibilidade_rel%C3%A2mpago.py)
## O que o programa faz?

Ao receber o nome de um produto e o CEP do usuário, o "Detetive de Preços" mobiliza uma equipe de quatro agentes especializados para:

1.  **Validar e Detalhar:** O primeiro agente verifica a validade do CEP, identifica a localização (cidade/estado) e refina a descrição do produto para buscas mais precisas, utilizando a busca do Google.
2.  **Buscar em Lojas Físicas:** O segundo agente, com base na localização e no produto refinado, procura por lojas físicas na região que vendem o item, tentando identificar preços e disponibilidade para retirada imediata, também com auxílio da busca do Google.
3.  **Buscar Ofertas Online:** O terceiro agente foca em encontrar o produto em lojas online, comparando preços, estimativas de entrega rápida e buscando por cupons de desconto aplicáveis, através da busca do Google.
4.  **Consolidar e Recomendar:** O quarto e último agente analisa todas as informações coletadas pelos agentes anteriores (sem usar a internet diretamente nesta etapa) e apresenta um relatório final ao usuário. Este relatório destaca as melhores opções para compra imediata, as melhores ofertas online e a opção mais barata no geral, além de observações relevantes.

## Principais Características

*   **Múltiplos Agentes de IA:** Utiliza uma arquitetura de múltiplos agentes, onde cada um possui uma especialidade e colabora para um resultado final mais completo.
*   **Integração com Google Search:** Os agentes de busca utilizam a ferramenta `google_search` (disponibilizada pelo ADK) para acessar informações atualizadas da internet.
*   **Foco na Praticidade:** Projetado para resolver uma necessidade cotidiana: encontrar um produto rapidamente e com o melhor custo-benefício.
*   **Interação Simples:** Requer apenas o nome do produto e o CEP como entrada.
*   **Saída Organizada:** Apresenta os resultados de forma clara e estruturada em Markdown.
*   **Controle de Visualização:** O usuário pode optar por ver apenas o relatório final ou acompanhar os resultados de cada agente intermediário, permitindo um entendimento detalhado do processo ou uma visualização mais direta.
*   **Rastreabilidade (Opcional):** Quando a visualização dos agentes intermediários está ativa, é possível ver as fontes e termos de busca que os agentes relatam ter utilizado, oferecendo uma ideia de como as informações foram obtidas.
*   **Desenvolvido para Google Colab:** O script é otimizado para execução em ambientes Google Colaboratory, utilizando `userdata` para gerenciamento de API Keys.

## Como Usar

1.  **Configurar a API Key:**
    *   Abra o notebook no Google Colab.
    *   No menu à esquerda, clique no ícone de chave (Secrets).
    *   Adicione um novo secret com o nome `GOOGLE_API_KEY` e cole sua chave da API do Google Gemini no valor.
2.  **Instalar Dependências:** Execute a primeira célula do notebook para instalar as bibliotecas necessárias (`google-genai`, `google-adk`, `requests`).
3.  **Executar o Programa:** Rode todas as células do notebook.
4.  **Fornecer Entradas:** O programa solicitará:
    *   O nome do produto que você procura.
    *   O seu CEP (para busca local).
    *   Se deseja ver os resultados dos agentes intermediários.
5.  **Analisar o Resultado:** O programa exibirá as informações coletadas e o relatório final do "Detetive de Preços".

---
