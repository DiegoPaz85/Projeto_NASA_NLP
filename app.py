import en_core_web_sm
import streamlit as st
import requests
import pandas as pd
import spacy
from spacy import displacy
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import os


# ==============================================================================
# CONFIGURAÇÃO INICIAL
# ==============================================================================

st.set_page_config(page_title="NASA NLP Dashboard", layout="wide", page_icon="🚀")

# Sistema Híbrido de Chaves (Nuvem vs Local):
if "NASA_API_KEY" in st.secrets:
    # Se estiver rodando na Nuvem, pega a chave dos Segredos do Streamlit
    API_KEY = st.secrets["NASA_API_KEY"]
else:
    # Se estiver rodando no seu computador (Local), usa o .env
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("NASA_API_KEY")

# ==============================================================================
# FUNÇÕES COM CACHE (Para máxima performance)
# ==============================================================================
@st.cache_resource
@st.cache_resource
@st.cache_resource
def carregar_modelo_spacy():
    """Carrega o modelo de NLP importado diretamente da memória."""
    return en_core_web_sm.load()

@st.cache_data(ttl=3600) # O cache dura 1 hora
def extrair_dados_nasa(quantidade=30):
    """Extrai os dados da API da NASA."""
    url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}&count={quantidade}"
    resposta = requests.get(url)
    if resposta.status_code == 200:
        df = pd.DataFrame(resposta.json())
        return df[['date', 'title', 'explanation', 'url']]
    return pd.DataFrame()

# Carregando as ferramentas
nlp = carregar_modelo_spacy()
df_apod = extrair_dados_nasa(30) # Puxando 30 imagens/textos

# ==============================================================================
# INTERFACE DO USUÁRIO (O que aparece na tela)
# ==============================================================================
st.title("🌌 NASA Text Analytics Dashboard")
st.markdown("Uma aplicação interativa de **Processamento de Linguagem Natural** sobre o cosmos.")

st.sidebar.header("Painel de Controle")
st.sidebar.write("Selecione um dos textos baixados da API:")

# Cria um menu dropdown na barra lateral com os títulos das imagens
titulo_selecionado = st.sidebar.selectbox("Escolha a Publicação:", df_apod['title'])

# Filtra o DataFrame para pegar apenas a linha que o usuário escolheu
linha_selecionada = df_apod[df_apod['title'] == titulo_selecionado].iloc[0]

# --- SEÇÃO 1: A PUBLICAÇÃO ---
col1, col2 = st.columns([1, 2]) # Divide a tela em duas colunas (a segunda é o dobro da primeira)

with col1:
    st.subheader(linha_selecionada['title'])
    st.image(linha_selecionada['url'], caption=linha_selecionada['date'], use_column_width=True)

with col2:
    st.subheader("Extração de Entidades Nomeadas (NER)")
    texto_original = linha_selecionada['explanation']
    
    # Processa o texto escolhido
    doc = nlp(texto_original)
    
    # Renderiza o texto colorido do displacy como HTML dentro do Streamlit!
    html_ner = displacy.render(doc, style="ent", page=True)
    
    # Usamos um componente especial para embutir o HTML
    st.components.v1.html(html_ner, height=400, scrolling=True)

# --- SEÇÃO 2: ANÁLISE GERAL (Gráficos) ---
st.divider() # Linha horizontal
st.subheader("📊 Ranking do Corpus (Últimos 30 Textos)")

# Extração rápida em massa para o gráfico
todas_orgs = []
todos_locais = []

for texto in df_apod['explanation']:
    if isinstance(texto, str):
        doc_lote = nlp(texto)
        for ent in doc_lote.ents:
            if ent.label_ == "ORG":
                todas_orgs.append(ent.text.strip().replace('\n', ' '))
            elif ent.label_ in ["GPE", "LOC"]:
                todos_locais.append(ent.text.strip().replace('\n', ' '))

# Configurando o gráfico do Seaborn
sns.set_theme(style="whitegrid", palette="pastel")
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

df_orgs = pd.DataFrame(Counter(todas_orgs).most_common(10), columns=['Organização', 'Citações'])
df_locais = pd.DataFrame(Counter(todos_locais).most_common(10), columns=['Local', 'Citações'])

sns.barplot(data=df_orgs, x='Citações', y='Organização', ax=axes[0], color='#3498db')
axes[0].set_title('Top 10 Organizações')

sns.barplot(data=df_locais, x='Citações', y='Local', ax=axes[1], color='#e74c3c')
axes[1].set_title('Top 10 Locais')

plt.tight_layout()
# Manda o gráfico do Matplotlib direto para a tela do Streamlit
st.pyplot(fig)