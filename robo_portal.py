import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import re

# ----------------------
# CONFIGURAÇÕES
# ----------------------
FEED_RSS = "https://g1.globo.com/rss/g1/"
TEMPLATE_HTML = "template.html"
SAIDA_HTML = "index.html"
IMAGEM_PADRAO = "https://picsum.photos/id/237/800/500"  # Placeholder elegante

# ----------------------
# FUNÇÕES AUXILIARES
# ----------------------
def data_atual_por_extenso():
    """Retorna data atual em português, por extenso"""
    meses = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    dias_semana = [
        "Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira",
        "Quinta-feira", "Sexta-feira", "Sábado"
    ]
    agora = datetime.now()
    return f"{dias_semana[agora.weekday()]}, {agora.day} de {meses[agora.month-1]} de {agora.year}"

def extrair_imagem_do_conteudo(conteudo):
    """Busca primeira imagem .jpg/.png dentro do conteúdo da notícia"""
    padrao = re.search(r'<img[^>]+src="([^"]+\.(jpg|png))"', conteudo or "", re.IGNORECASE)
    if padrao:
        return padrao.group(1)
    return IMAGEM_PADRAO

def tempo_publicacao(data_publicacao):
    """Retorna tempo aproximado desde a publicação"""
    try:
        pub = datetime(*data_publicacao[:6])
        delta = datetime.now() - pub
        if delta.days > 0:
            return f"há {delta.days} dia{'s' if delta.days > 1 else ''}"
        minutos = delta.seconds // 60
        if minutos < 60:
            return f"há {minutos} min"
        horas = minutos // 60
        return f"há {horas} h"
    except:
        return "há pouco tempo"

# ----------------------
# LEITURA DO FEED RSS
# ----------------------
print("🔍 Lendo feed RSS...")
feed = feedparser.parse(FEED_RSS)
if not feed.entries:
    print("❌ Nenhuma notícia encontrada no feed. Usando dados de exemplo.")
    exit()

# ----------------------
# CARREGAR TEMPLATE HTML
# ----------------------
print("📄 Carregando template...")
with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

# ----------------------
# ATUALIZAR ELEMENTOS
# ----------------------

# Data do cabeçalho
el_data = soup.find(id="header-date")
if el_data:
    el_data.string = data_atual_por_extenso()

# Ano no rodapé
el_ano = soup.find(id="copyright-year")
if el_ano:
    el_ano.string = str(datetime.now().year)

# Faixa de notícias urgentes
el_ticker = soup.find(id="ticker-text")
if el_ticker and len(feed.entries) >= 5:
    titulos = [entry.title for entry in feed.entries[:5]]
    el_ticker.string = " · ".join(titulos)

# Notícia principal
el_destaque = soup.find(id="featured-news")
if el_destaque and len(feed.entries) >= 1:
    principal = feed.entries[0]
    categoria = principal.get("category", "Geral")
    resumo = BeautifulSoup(principal.get("summary", ""), "lxml").get_text(strip=True)[:250] + "..."
    imagem = extrair_imagem_do_conteudo(principal.get("summary", ""))

    el_destaque.find(id="featured-category").string = categoria
    el_destaque.find(id="featured-datetime").string = tempo_publicacao(principal.published_parsed)
    el_destaque.find(id="featured-title").string = principal.title
    el_destaque.find(id="featured-summary").string = resumo
    el_destaque.find(id="featured-img-link")["href"] = principal.link
    el_destaque.find(id="featured-img")["src"] = imagem
    el_destaque.find(id="featured-img")["alt"] = principal.title
    el_destaque.find(id="featured-link")["href"] = principal.link

# Grade de últimas notícias
el_grade = soup.find(id="news-grid")
if el_grade and len(feed.entries) >= 7:
    el_grade.clear()  # remove cards antigos
    for noticia in feed.entries[1:7]:
        categoria = noticia.get("category", "Geral")
        imagem = extrair_imagem_do_conteudo(noticia.get("summary", ""))

        card = soup.new_tag("article", attrs={"class": "news-card"})
        card.append(BeautifulSoup(f'''
            <img class="card-img" src="{imagem}" alt="{noticia.title}">
            <div class="card-body">
                <span class="card-category">{categoria}</span>
                <h3 class="card-title">{noticia.title}</h3>
                <a href="{noticia.link}" class="card-link">Leia mais <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
            </div>
        ''', "lxml"))
        el_grade.append(card)

# Lista de mais lidas
el_mais_lidas = soup.find(id="most-read-list")
if el_mais_lidas and len(feed.entries) >= 12:
    el_mais_lidas.clear()
    for pos, noticia in enumerate(feed.entries[7:12], start=1):
        item = soup.new_tag("li", attrs={"class": "most-read-item"})
        item.append(BeautifulSoup(f'''
            <span class="read-position">{pos}</span>
            <div class="read-info">
                <h4>{noticia.title}</h4>
                <span class="read-time">{tempo_publicacao(noticia.published_parsed)}</span>
            </div>
        ''', "lxml"))
        el_mais_lidas.append(item)

# ----------------------
# SALVAR ARQUIVO FINAL
# ----------------------
with open(SAIDA_HTML, "w", encoding="utf-8") as f:
    f.write(str(soup.prettify()))

print("✅ Arquivo index.html gerado com sucesso!")
