# Certifique-se de que as bibliotecas estão instaladas no ambiente Colab
!pip -q install google-genai google-adk requests

# Configura a API Key do Google Gemini
import os
from google.colab import userdata

# Tenta obter a API key. Se não estiver definida, avisa o usuário.
try:

    os.environ["GOOGLE_API_KEY"] = userdata.get('GOOGLE_API_KEY')
    if os.environ["GOOGLE_API_KEY"] is None:
        raise ValueError("GOOGLE_API_KEY não encontrada no Colab Secrets.")
    print("GOOGLE_API_KEY configurada com sucesso.") # Opcional: Descomente para confirmar
except Exception as e:
    print(f"Erro ao configurar GOOGLE_API_KEY: {e}")
    print("Por favor, certifique-se de que a GOOGLE_API_KEY está definida nos Secrets do Colab (chave: GOOGLE_API_KEY).")
    print("O programa continuará, mas as chamadas à API Gemini falharão se a chave não estiver correta.")

# Configura o cliente da SDK do Gemini (embora o ADK o gerencie internamente para Agents)
from google import genai

MODEL_ID_AGENT = "gemini-2.0-flash" # Usando o mesmo modelo do exemplo do usuário

# Imports do ADK e outros utilitários
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types as genai_types # Renomeado para evitar conflito
from datetime import date
import textwrap
from IPython.display import display, Markdown
import warnings

warnings.filterwarnings("ignore") # Como no original

# Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final
def call_agent(agent: Agent, message_text: str) -> str:
    session_service = InMemorySessionService()
    session = session_service.create_session(app_name=agent.name, user_id="detetive_user", session_id="preco_session_01") # Session ID único
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=message_text)])

    final_response = ""
    for event in runner.run(user_id="detetive_user", session_id="preco_session_01", new_message=content):
        if event.is_final_response():
          for part in event.content.parts:
            if part.text is not None:
              final_response += part.text
              final_response += "\n"

    if not final_response.strip() and agent.tools: # Se não houve resposta e o agente tinha ferramentas
        print(f"⚠️ Atenção: O agente {agent.name} não retornou uma resposta final substancial. Verifique as instruções e se a ferramenta google_search foi chamada corretamente.")
        print(f"   Input para o agente: '{message_text[:150]}...'")

    return final_response.strip()

# Função auxiliar para exibir texto formatado em Markdown no Colab
def to_markdown(text):
  if not isinstance(text, str):
      text = str(text)
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

#################################################################
# --- Agente 1: Validador de Produto e Localização --- #
#################################################################
def agente_validador_detalhador(produto_bruto: str, cep_bruto: str):
    validador_agente = Agent(
        name="agente_validador_detalhador",
        model=MODEL_ID_AGENT,
        instruction=f"""
        Você é um assistente de pesquisa inicial. Sua tarefa é usar a ferramenta de busca do Google (google_search) para processar um produto e um CEP.
        Produto fornecido: '{produto_bruto}'
        CEP fornecido: '{cep_bruto}'

        1.  **Análise do CEP:** Verifique se o CEP '{cep_bruto}' é um formato válido para o Brasil (8 dígitos numéricos). Usando a busca, tente encontrar a cidade e o estado correspondentes a este CEP. Se o CEP parecer inválido ou não for encontrado, declare isso.
        2.  **Análise do Produto:** Para o produto '{produto_bruto}', faça uma busca rápida para entender melhor suas características principais, marca, ou modelos comuns. Se o nome for muito genérico (ex: "notebook"), liste algumas características chave a considerar (ex: "Notebook para jogos? Para trabalho? Qual tamanho de tela?"). Se for específico (ex: "Samsung Galaxy S23 Ultra 256GB"), confirme suas principais características.

        **Formato da Resposta Obrigatório:**
        ```text
        **Análise do Produto e Localização:**

        **Produto Analisado:** [Nome do produto, possivelmente com sugestões de refino, marcas ou características chave identificadas. Se for específico, confirme.]
        **Termo de Produto para Próximos Agentes:** [Use o nome do produto refinado aqui, o mais específico possível para buscas futuras.]

        **CEP Analisado:** {cep_bruto}
        **Localização Encontrada:** [Cidade, Estado] (ou "CEP inválido/não encontrado" ou "Informação de cidade/estado não encontrada para o CEP.")

        **Observações/Sugestões para o Produto:** [Breves comentários, como variações comuns, ou se mais detalhes do usuário seriam úteis.]

        **Fontes e Buscas (Agente Validador):**
        *   Termos de busca usados: [Liste 2-3 principais termos que você usou no google_search]
        *   Principais fontes consultadas: [Liste 1-2 sites ou tipos de sites que foram úteis]
        ```
        Seja conciso e direto ao ponto.
        """,
        description="Agente que valida CEP, refina descrição do produto e identifica localização via Google Search.",
        tools=[google_search]
    )
    entrada_agente = f"Por favor, processe o produto '{produto_bruto}' e o CEP '{cep_bruto}' conforme as instruções."
    resultado_validacao = call_agent(validador_agente, entrada_agente)
    return resultado_validacao

#################################################################
# --- Agente 2: Buscador de Lojas Físicas e Estoque Próximo --- #
#################################################################
def agente_buscador_lojas_fisicas(info_completa_agente1: str):
    buscador_fisico_agente = Agent(
        name="agente_buscador_lojas_fisicas",
        model=MODEL_ID_AGENT,
        instruction=f"""
        Você é um especialista em encontrar produtos em lojas físicas locais.
        Abaixo estão as informações validadas por um agente anterior. Extraia delas o 'Termo de Produto para Próximos Agentes' e a 'Localização Encontrada (Cidade, Estado)'.
        Se a localização for "CEP inválido" ou "não encontrada", informe que não é possível prosseguir com a busca local e pare.

        **Informações Validadas do Agente Anterior:**
        {info_completa_agente1}

        Usando o produto e a localização extraídos, sua tarefa é usar a ferramenta `google_search` para encontrar:
        1.  Lojas físicas na cidade/região indicada que vendem o produto.
        2.  Se possível, o preço em cada loja.
        3.  Se possível, informações sobre disponibilidade para retirada imediata ("retirar hoje", "em estoque", "disponível para coleta").

        Liste até 3-4 opções relevantes. Se não encontrar informações de estoque, apenas liste a loja e o preço, se disponíveis.

        **Formato da Resposta Obrigatório:**
        ```text
        **Busca em Lojas Físicas ([Produto Extraído] em [Localização Extraída]):**

        *   **Loja:** [Nome da Loja 1]
            *   Endereço: [Endereço, se encontrado]
            *   Preço: [R$ XX,XX, se encontrado]
            *   Disponibilidade: [Informação sobre estoque/retirada, se encontrada]
        *   **Loja:** [Nome da Loja 2]
            *   ... (repetir)

        (Se nenhuma opção for encontrada: "Nenhuma loja física encontrada com o produto na região pesquisada com base nas informações disponíveis.")

        **Fontes e Buscas (Agente Lojas Físicas):**
        *   Termos de busca usados: [Liste 2-3 principais termos]
        *   Principais fontes consultadas: [Liste 1-2 sites ou tipos de sites]
        ```
        """,
        description="Agente que busca o produto em lojas físicas próximas e verifica estoque, usando Google Search.",
        tools=[google_search]
    )
    entrada_agente = f"Com base nas informações validadas fornecidas, realize a busca em lojas físicas: {info_completa_agente1}"
    resultados_lojas = call_agent(buscador_fisico_agente, entrada_agente)
    return resultados_lojas

#####################################################################
# --- Agente 3: Buscador de Ofertas Online e Cupons --- #
#####################################################################
def agente_buscador_ofertas_online(info_completa_agente1: str):
    buscador_online_agente = Agent(
        name="agente_buscador_ofertas_online",
        model=MODEL_ID_AGENT,
        instruction=f"""
        Você é um especialista em encontrar as melhores ofertas online para produtos, com foco em entrega rápida e cupons de desconto.
        Abaixo estão as informações validadas por um agente anterior. Extraia delas o 'Termo de Produto para Próximos Agentes'.

        **Informações Validadas do Agente Anterior:**
        {info_completa_agente1}

        Usando o produto extraído, sua tarefa é usar a ferramenta `google_search` para encontrar:
        1.  Lojas online que vendem o produto com opções de entrega rápida (ex: entrega em até 2-5 dias úteis no Brasil).
        2.  O preço do produto em cada loja online.
        3.  Cupons de desconto aplicáveis para essas lojas ou para o produto específico.

        Liste até 3-4 opções relevantes.

        **Formato da Resposta Obrigatório:**
        ```text
        **Busca de Ofertas Online ([Produto Extraído]):**

        *   **Loja Online:** [Nome da Loja 1]
            *   Produto na Loja: [Nome do Produto na Loja, se variar do termo buscado]
            *   Preço: [R$ XX,XX]
            *   Entrega Estimada: [Informação, se encontrada, ex: 'Até X dias úteis']
            *   Cupom: [Código do Cupom ou "Nenhum cupom evidente encontrado"]
        *   **Loja Online:** [Nome da Loja 2]
            *   ... (repetir)

        (Se nenhuma opção for encontrada: "Nenhuma oferta online relevante com entrega rápida encontrada para o produto.")

        **Fontes e Buscas (Agente Ofertas Online):**
        *   Termos de busca usados: [Liste 2-3 principais termos]
        *   Principais fontes consultadas: [Liste 1-2 sites ou tipos de sites]
        ```
        """,
        description="Agente que busca ofertas online, focando em entrega rápida e cupons, usando Google Search.",
        tools=[google_search]
    )
    entrada_agente = f"Com base nas informações validadas fornecidas, realize a busca de ofertas online: {info_completa_agente1}"
    resultados_online = call_agent(buscador_online_agente, entrada_agente)
    return resultados_online

####################################################################
# --- Agente 4: Consolidador e Recomendador --- #
####################################################################
def agente_consolidador_recomendador(produto_original_usuario: str, info_validada_ag1: str, resultados_lojas_fisicas: str, resultados_ofertas_online: str):
    consolidador_agente = Agent(
        name="agente_consolidador_recomendador",
        model=MODEL_ID_AGENT,
        instruction=f"""
        Você é um assistente de compras inteligente. Seu trabalho é analisar os resultados das buscas de lojas físicas e ofertas online para um produto e fornecer um resumo e recomendações claras para o usuário.
        **Não use ferramentas de busca (google_search)**, apenas processe o texto fornecido.

        Produto Originalmente Solicitado pelo Usuário: '{produto_original_usuario}'
        Informações Validadas pelo Agente 1 (contém o produto refinado e localização):
        {info_validada_ag1}

        Resultados da Busca em Lojas Físicas (Agente 2):
        {resultados_lojas_fisicas}

        Resultados da Busca de Ofertas Online (Agente 3):
        {resultados_ofertas_online}

        Com base exclusivamente nessas informações, forneça:
        1.  Um breve resumo das melhores opções encontradas (máximo 2-3 no total), considerando preço, disponibilidade/rapidez e conveniência.
        2.  Destaque a 'Melhor Opção para Hoje' (se houver loja física com disponibilidade imediata e bom preço).
        3.  Destaque a 'Melhor Opção Online' (considerando preço + frete/entrega rápida + cupons).
        4.  Destaque a 'Opção Mais Barata no Geral' (se diferente das anteriores, mesmo com entrega mais longa ou se for em loja física).

        Seja objetivo e claro. Se as buscas não retornaram resultados úteis em alguma categoria, indique isso de forma neutra.
        Use o "Termo de Produto para Próximos Agentes" (da saída do Agente 1) como o nome do produto nas suas recomendações.

        **Formato da Resposta Obrigatório:**
        ```text
        **Relatório Final do Detetive de Preços para '[Termo de Produto extraído da info_validada_ag1]'**

        Analisando as buscas para o produto originalmente solicitado: '{produto_original_usuario}'.

        *   **Opção Destaque para Compra Imediata (Lojas Físicas):**
            *   [Detalhes da melhor opção física encontrada, ex: Loja X, Preço Y, Disponível hoje. Ou: "Nenhuma opção clara para compra imediata identificada nas buscas."].

        *   **Opção Destaque Online (Equilíbrio Preço/Rapidez):**
            *   [Detalhes da melhor opção online, ex: Loja Online A, Preço B, Entrega C, Cupom D. Ou: "Nenhuma opção online com bom equilíbrio preço/rapidez destacada nas buscas."].

        *   **Opção Mais Barata Identificada (Geral):**
            *   [Detalhes da opção mais barata, seja física ou online, ex: Loja Z, Preço W. Ou: "Não foi possível determinar uma opção claramente mais barata com os dados fornecidos."].

        **Observações Gerais do Detetive:**
        *   [Qualquer ponto relevante, como: "A busca em lojas físicas para [Cidade] retornou poucas opções." ou "Vários cupons encontrados para compras online." ou "Produto parece ter alta variação de preço." Se não houver nada relevante, pode omitir ou dizer "Nenhuma observação adicional."].
        ```
        """,
        description="Agente que consolida informações e recomenda as melhores opções de compra, sem usar busca."
        # Este agente NÃO usa tools.
    )
    entrada_agente = (
        f"Produto Original: {produto_original_usuario}\n\n"
        f"Info Agente 1:\n{info_validada_ag1}\n\n"
        f"Resultados Lojas Físicas:\n{resultados_lojas_fisicas}\n\n"
        f"Resultados Ofertas Online:\n{resultados_ofertas_online}"
    )
    recomendacao_final = call_agent(consolidador_agente, entrada_agente)
    return recomendacao_final

# --- Fluxo Principal do Detetive de Preços ---
print("🚀 Iniciando o Detetive de Preços e Disponibilidade Relâmpago 🚀")

produto_desejado_usuario = input("❓ Por favor, digite o NOME do produto que você procura: ")
cep_usuario_input = input("🏠 Por favor, digite o seu CEP (apenas números, ex: 01000000) para busca local: ")

mostrar_intermediarios = False
while True:
    escolha_ver_intermediarios = input("👁️ Mostrar o resultado dos agentes intermediários (Sim/Não/S/N)? [Enter para Não]: ").strip().lower()
    if escolha_ver_intermediarios in ["sim", "s"]:
        mostrar_intermediarios = True
        break
    elif escolha_ver_intermediarios in ["não", "nao", "n", ""]: # "" para Enter
        mostrar_intermediarios = False
        break
    else:
        print("⚠️ Opção inválida. Por favor, digite Sim, Não, S ou N.")

if not produto_desejado_usuario or not cep_usuario_input:
    print("\n⚠️ Você precisa informar o nome do produto e o CEP para o detetive trabalhar!")
else:
    print(f"\n🔍 Buscando por '{produto_desejado_usuario}' perto do CEP '{cep_usuario_input}'. Aguarde, isso pode levar alguns instantes...\n")

    # --- Agente 1: Validador e Detalhador ---
    if mostrar_intermediarios:
        print("--- 🕵️ Agente 1: Validando Produto e Localização ---")
    info_validada_ag1 = agente_validador_detalhador(produto_desejado_usuario, cep_usuario_input)
    if mostrar_intermediarios:
        display(to_markdown(info_validada_ag1))
        print("--------------------------------------------------------------\n")

    # Verifica se a validação foi bem-sucedida antes de prosseguir com buscas dependentes
    pode_buscar_local = "CEP inválido" not in info_validada_ag1 and "não encontrada para o CEP" not in info_validada_ag1

    # --- Agente 2: Buscador de Lojas Físicas ---
    if pode_buscar_local and info_validada_ag1.strip():
        if mostrar_intermediarios:
            print("--- 🏪 Agente 2: Buscando em Lojas Físicas Próximas ---")
        resultados_lojas_fisicas = agente_buscador_lojas_fisicas(info_validada_ag1)
        if mostrar_intermediarios:
            display(to_markdown(resultados_lojas_fisicas))
    elif not info_validada_ag1.strip():
        if mostrar_intermediarios:
            print("--- 🏪 Agente 2: Busca em Lojas Físicas Pulada (Agente 1 não retornou informações) ---")
        resultados_lojas_fisicas = "Busca em lojas físicas não realizada devido à ausência de informações do agente validador."
        if mostrar_intermediarios:
            display(to_markdown(resultados_lojas_fisicas))
    else:
        if mostrar_intermediarios:
            print("--- 🏪 Agente 2: Busca em Lojas Físicas Pulada (Problema com CEP na validação) ---")
        resultados_lojas_fisicas = "Busca em lojas físicas não realizada devido a CEP inválido ou não encontrado pelo agente validador."
        if mostrar_intermediarios:
            display(to_markdown(resultados_lojas_fisicas))
    if mostrar_intermediarios:
        print("--------------------------------------------------------------\n")

    # --- Agente 3: Buscador de Ofertas Online ---
    if info_validada_ag1.strip():
        if mostrar_intermediarios:
            print("--- 💻 Agente 3: Buscando Ofertas Online e Cupons ---")
        resultados_ofertas_online = agente_buscador_ofertas_online(info_validada_ag1)
        if mostrar_intermediarios:
            display(to_markdown(resultados_ofertas_online))
    else:
        if mostrar_intermediarios:
            print("--- 💻 Agente 3: Busca de Ofertas Online Pulada (Agente 1 não retornou informações) ---")
        resultados_ofertas_online = "Busca de ofertas online não realizada devido à ausência de informações do agente validador."
        if mostrar_intermediarios:
            display(to_markdown(resultados_ofertas_online))
    if mostrar_intermediarios:
        print("--------------------------------------------------------------\n")

    # --- Agente 4: Consolidador e Recomendador (SEMPRE EXIBIDO) ---
    if info_validada_ag1.strip():
        print("--- 🏆 Agente 4: Consolidando Resultados e Recomendando ---")
        recomendacao_final = agente_consolidador_recomendador(
            produto_desejado_usuario,
            info_validada_ag1,
            resultados_lojas_fisicas,
            resultados_ofertas_online
        )
        display(to_markdown(recomendacao_final))
    else:
        print("--- 🏆 Agente 4: Consolidação Pulada (Agente 1 não retornou informações) ---")
        display(to_markdown("Não foi possível gerar recomendações pois o agente inicial de validação não forneceu dados."))
    print("--------------------------------------------------------------\n")

    print("✨ Detetive de Preços concluiu a investigação! ✨")