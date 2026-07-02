from __future__ import annotations

import csv
import json
import os
import re
import sys
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUTPUTS = ROOT / "outputs"
SITE = OUTPUTS / "achadinhos-delas.html"
PUBLISH_SITE = OUTPUTS / "publicar-achadinhos-delas" / "index.html"
DOCS_SITE = ROOT / "docs" / "index.html"
DOWNLOADS = Path.home() / "Downloads"
FEED_URLS = WORK / "feed_urls.txt"
FEED_DIR = WORK / "downloaded-feeds"
LOG = WORK / "auto-update.log"
MANUAL_PRODUCTS = WORK / "manual_products.json"


def norm(value: object) -> str:
    text = str(value or "").lower()
    return "".join(
        char for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def money(value: object) -> float | None:
    try:
        number = float(str(value or "").replace(",", "."))
    except ValueError:
        return None
    return number if number > 0 else None


def clean_title(value: object) -> str:
    title = re.sub(r"\s+", " ", str(value or "")).strip().replace("\ufffd", "")
    title = re.sub(r"^[\[\(]*\s*promo[cç][aã]o\s*[-:|]*\s*", "", title, flags=re.I)
    return title[:124].strip(" -|,")


CAT_TERMS = {
    "beleza": [
        "gloss", "batom", "lip", "labial", "delineador", "rimel", "rímel",
        "mascara de cilios", "máscara de cílios", "eyelash", "maquiagem",
        "sombra", "blush", "base em gel", "base maquiagem", "corretivo",
        "contorno", "iluminador", "pincel de maquiagem", "esponja de maquiagem",
        "sobrancelha", "cilios", "cílios", "unha", "esmalte", "cuticula",
        "cutícula", "manicure", "pedicure", "lixa para unha", "alicate de cuticula",
        "pinça sobrancelha", "pinca sobrancelha", "curvex", "gel nude",
        "unhas em gel", "adesivo de unha", "carimbo de sobrancelha",
        "henna sobrancelha",
    ],
    "acessorios": [
        "brinco", "colar", "pulseira", "anel", "argola", "choker",
        "tornozeleira", "tiara", "presilha", "piranha", "xuxinha",
        "grampo de cabelo", "broche feminino", "oculos de sol feminino",
        "óculos de sol feminino", "elastico de cabelo", "elástico de cabelo",
        "laço de cabelo", "laco de cabelo", "scrunchie", "fivela de cabelo",
    ],
    "bolsas": [
        "bolsa feminina", "bolsa pequena", "bolsa transversal", "bolsa de lado",
        "bolsa tiracolo", "necessaire", "nécessaire", "carteira feminina",
        "porta moeda feminino", "pochete feminina", "clutch",
    ],
    "roupas": [
        "vestido feminino", "blusa feminina", "cropped", "saia feminina",
        "short feminino", "calça feminina", "calca feminina", "regata feminina",
        "top feminino", "kimono feminino", "cardigan feminino", "body feminino",
        "t-shirt feminina", "camiseta feminina", "conjunto feminino", "moda feminina",
    ],
    "conforto": [
        "lingerie", "sutia", "sutiã", "calcinha", "meia feminina", "meia-calça",
        "meia calca", "pijama feminino", "camisola", "robe feminino",
        "cinta modeladora", "short modelador", "top sem costura", "bojo",
    ],
}

BAD_TERMS = [
    "masculino", "homem", "menino", "menina", "infantil", "kids", "baby",
    "bebe", "criança", "crianca", "pet", "cachorro", "gato", "carro", "moto",
    "bicicleta", "ferramenta", "parafuso", "eletrico", "eletrônico", "eletronico",
    "lampada", "lâmpada", "farol", "philips", "iphone", "samsung", "xiaomi",
    "celular", "tablet", "notebook", "mouse", "teclado", "cabo usb", "fone",
    "capinha", "magsafe", "camera", "papelaria", "escolar", "livro", "gibi",
    "compasso", "caneta hidrografica", "caneta hidrográfica", "brush sign pen",
    "cola em fita", "cola", "pentel", "cortador redondo", "alimento", "biscoito",
    "cookie", "bauducco", "gluten", "glúten", "ração", "racao", "cozinha",
    "panela", "garrafa", "copo", "jardim", "brinquedo", "desinfetante", "limpeza",
    "urca", "reparo", "borracha", "trampolim", "pintura artistica",
    "pintura artística", "artesanato", "bola", "futsal", "campo", "bomba de ar",
    "wap", "vedacao", "vedação", "valente", "excellent", "bravo", "filtro",
    "torneira", "mangueira", "automotivo", "pneu", "capacete", "controle remoto",
    "pilha", "bateria", "carregador", "usb", "hdmi", "jogo", "gamer", "erotica",
    "erótico", "algema", "vibrador", "plug anal", "for sexy", "camisinha",
    "preservativo", "fantasia cachorra", "desentupidor", "coletor de cabelos",
    "estilete", "brigadeiro", "docinho",
]

REMOVE_TERMS = [
    "sabonete", "creme dental", "pasta de dente", "pasta dental", "colgate",
    "closeup", "oral", "enxaguatorio", "bucal", "escova dental", "fio dental",
    "papel higienico", "hastes flexiveis", "cotonete", "alcool em gel",
    "desodorante", "antitranspirante", "repelente", "lysoform", "absorvente",
    "protetor diario", "lenço umedecido", "lenco umedecido", "lenço de papel",
    "lenco de papel", "touca descartavel", "luva latex", "protetor auricular",
    "tampoes de ouvido", "agua oxigenada", "talco", "banila co clean it zero cleansing balm",
    "cleanser", "cleansing", "shampoo", "condicionador", "creme de pentear",
    "tratamento capilar", "papel", "algodao apolo",
]

CATEGORY_ORDER = {"beleza": 0, "acessorios": 1, "bolsas": 2, "roupas": 3, "conforto": 4}

EXTRA_BAD_TERMS = [
    "adaptador", "adesivo parede", "agulha", "alicate universal", "antena",
    "ar condicionado", "bandeja", "barbeador", "batedor", "bebedouro", "bico",
    "bobina", "borracharia", "botao", "cabide", "caderno", "cadeado", "caixa",
    "caneca", "carimbo escolar", "cartolina", "cartucho", "cha ", "chá ",
    "chave", "clips", "clip de cabo", "clip magnetico", "coletor de cabelo",
    "colher", "controle", "cortador", "desentupidor", "disjuntor", "dvd",
    "embalagem", "envelope", "estojo escolar", "etiqueta", "faca", "fio",
    "forminha", "grampeador", "grampo para cabo", "grampo de aco", "impressora",
    "faber-castell", "fantasia", "halloween", "interruptor", "lampada",
    "lanterna", "lapis de cor", "leao", "luminaria", "makita", "marcador",
    "molde", "organizador de gaveta", "parafusadeira", "parafuso",
    "pasta em l", "pasta oficio", "phillips", "pote", "prato", "refil",
    "regua", "sanduba", "saco",
    "sacola", "squeeze", "suporte", "tesoura escolar", "tomada", "usb",
    "apple watch", "bts", "flanela magica", "porta malas", "p/vaso",
    "fecho de metal", "tela malha", "homens", "unissex", "termica",
    "térmica", "saude", "saúde", "expositor", "multilaser", "remedios",
    "remédios",
]

CATEGORY_BLOCKERS = {
    "beleza": [
        "sabonete", "dental", "colgate", "shampoo", "condicionador",
        "creme de pentear", "tratamento capilar", "vitamina", "d-pantenol",
        "cleansing", "desodorante", "absorvente", "banila", "co clean",
        "massageador", "touca descartavel", "protetor auricular",
        "faber-castell", "phillips", "makita", "parafusadeira",
        "organizador de cabos",
    ],
    "acessorios": [
        "cabo", "clips", "clip", "aco", "aço", "magnetico", "magnético",
        "parafuso", "chaveiro", "cabide", "grampo para", "suporte",
        "organizadora", "organizadores",
    ],
    "bolsas": [
        "saco", "sacola", "mochila infantil", "mochila escolar", "lancheira",
        "organizador", "estojo escolar", "pasta", "p/vaso", "fecho de metal",
        "tela malha", "espelho de bolsa", "pente", "termica", "térmica",
        "saude", "saúde", "expositor", "multilaser",
    ],
    "roupas": [
        "masculino", "infantil", "menino", "menina", "baby", "bebe",
        "fantasia", "uniforme",
    ],
    "conforto": [
        "erotico", "erótico", "sexy", "camisinha", "preservativo", "plug",
        "vibrador", "absorvente", "infantil", "masculino",
    ],
}


def log(message: str) -> None:
    WORK.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")


def feed_urls() -> list[str]:
    env_urls = os.environ.get("SHOPEE_FEED_URLS", "")
    if env_urls.strip():
        return [
            line.strip()
            for line in env_urls.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    if not FEED_URLS.exists():
        return []
    urls = []
    for line in FEED_URLS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def download_feeds(urls: list[str]) -> list[Path]:
    FEED_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, url in enumerate(urls, 1):
        target = FEED_DIR / f"feed-{index}.csv"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        if not data.startswith(b"\xef\xbb\xbf") and b"," not in data[:200]:
            raise RuntimeError(f"O link {index} nao retornou um CSV valido.")
        target.write_bytes(data)
        paths.append(target)
    return paths


def latest_downloaded_feeds() -> list[Path]:
    patterns = ["*Shopee Brasil - 2022*.csv", "*Shopee Oficial BR - 2022*.csv"]
    paths: list[Path] = []
    for pattern in patterns:
        matches = sorted(DOWNLOADS.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
        if matches:
            paths.append(matches[0])
    return paths


def has_any(text: str, terms: list[str]) -> bool:
    return any(norm(term) in text for term in terms)


def classify(row: dict[str, str]) -> str | None:
    title = norm(row.get("title", ""))
    desc = norm(row.get("description", ""))
    feed_categories = norm(" ".join([
        row.get("global_category1", ""),
        row.get("global_category2", ""),
        row.get("global_category3", ""),
    ]))
    full_text = " ".join([title, desc, feed_categories])

    title_priority = [
        ("bolsas", [
            "bolsa feminina", "bolsas femininas", "bolsa pequena",
            "bolsa transversal", "bolsa tiracolo", "bolsa de ombro",
            "bolsa de axila", "mini bag", "carteira feminina",
            "necessaire", "pochete feminina", "clutch",
        ]),
        ("roupas", ["vestido", "blusa", "cropped", "saia", "short feminino", "calca feminina", "regata", "camiseta feminina"]),
        ("conforto", ["lingerie", "sutia", "calcinha", "pijama", "meia-calca", "meia calca", "cinta modeladora"]),
        ("acessorios", ["brinco", "colar", "pulseira", "argola", "choker", "tornozeleira", "presilha", "piranha", "tiara"]),
    ]
    for category, terms in title_priority:
        if has_any(full_text, CATEGORY_BLOCKERS.get(category, [])):
            continue
        if any(term in title for term in terms):
            return category
    if re.search(r"\banel\b|\baneis\b|\ban[eé]is\b", title) and not any(term in title for term in ["maquiagem", "unha", "sobrancelha"]):
        return "acessorios"

    scores: dict[str, int] = {}
    for category, terms in CAT_TERMS.items():
        if has_any(full_text, CATEGORY_BLOCKERS.get(category, [])):
            continue

        score = 0
        normalized_terms = [norm(term) for term in terms]
        score += sum(8 for term in normalized_terms if term in title)
        score += sum(3 for term in normalized_terms if term in feed_categories)
        score += sum(1 for term in normalized_terms if term in desc)

        if category == "bolsas" and any(term in title for term in [
            "bolsa feminina", "bolsas femininas", "bolsa pequena",
            "bolsa transversal", "bolsa tiracolo", "bolsa de ombro",
            "bolsa de axila", "mini bag", "carteira feminina",
            "necessaire", "pochete feminina", "clutch",
        ]):
            score += 10
        if category == "roupas" and any(term in title for term in ["feminina", "moda feminina", "vestido", "blusa", "cropped", "saia"]):
            score += 3
        if category == "acessorios" and any(term in title for term in ["brinco", "colar", "pulseira", "anel", "presilha", "tiara"]):
            score += 7
        if category == "beleza" and any(term in title for term in ["maquiagem", "gloss", "batom", "unha", "cilios", "sobrancelha"]):
            score += 2

        if score:
            scores[category] = score

    if not scores:
        return None

    category, score = sorted(
        scores.items(),
        key=lambda item: (-item[1], CATEGORY_ORDER[item[0]]),
    )[0]
    return category if score >= 8 else None


def image_for(row: dict[str, str]) -> str:
    for key in ["image_link", "image_link_2", "image_link_3"]:
        value = str(row.get(key) or "").strip()
        if value.startswith("https://"):
            return value
    return ""


def link_for(row: dict[str, str]) -> str:
    for key in ["product_short link", "product_short_link", "offer_link", "link"]:
        value = str(row.get(key) or "").strip()
        if value.startswith("http"):
            return value
    return str(row.get("product_link") or "").strip()


def manual_products() -> list[dict[str, str]]:
    if not MANUAL_PRODUCTS.exists():
        return []
    try:
        data = json.loads(MANUAL_PRODUCTS.read_text(encoding="utf-8"))
    except Exception as error:
        log(f"Falha ao ler produtos manuais: {error}")
        return []

    required = {"name", "label", "category", "price", "desc", "budget", "image", "url"}
    products: list[dict[str, str]] = []
    for item in data:
        if isinstance(item, dict) and required.issubset(item):
            products.append({key: str(item[key]) for key in required})
    return products


def merge_manual_products(products: list[dict[str, str]]) -> list[dict[str, str]]:
    manual = manual_products()
    if not manual:
        return products
    seen_urls = {product["url"] for product in manual}
    seen_names = {norm(product["name"]) for product in manual}
    return manual + [
        product for product in products
        if product["url"] not in seen_urls and norm(product["name"]) not in seen_names
    ]


def desc_for(category: str, budget: str) -> str:
    if budget == "50":
        return {
            "beleza": "Maquiagem e unhas até R$50 para comprar com mais critério.",
            "acessorios": "Acessório feminino até R$50 para deixar o look mais completo.",
            "bolsas": "Bolsa feminina até R$50 para usar muito e pagar pouco.",
            "roupas": "Moda feminina até R$50 com cara de achado esperto.",
            "conforto": "Conforto feminino até R$50 para renovar os básicos.",
        }[category]
    return {
        "beleza": "Maquiagem, unhas e beleza para garimpar barato na Shopee.",
        "acessorios": "Acessório feminino para mudar o look gastando pouco.",
        "bolsas": "Bolsa ou carteira prática com preço de achadinho.",
        "roupas": "Moda feminina para comprar bonito gastando pouco.",
        "conforto": "Item de conforto feminino para o dia a dia.",
    }[category]


def build_products(feeds: list[Path]) -> list[dict[str, str]]:
    products: list[dict[str, str]] = []
    seen: set[str] = set()
    seen_titles: set[str] = set()
    for feed in feeds:
        with feed.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                price = money(row.get("sale_price")) or money(row.get("price"))
                if price is None or price > 50:
                    continue
                if "\ufffd" in str(row.get("title") or ""):
                    continue
                title = clean_title(row.get("title"))
                if len(title) < 5:
                    continue
                text = norm(" ".join([
                    title,
                    row.get("description", ""),
                    row.get("global_category1", ""),
                    row.get("global_category2", ""),
                    row.get("global_category3", ""),
                ]))
                if any(norm(term) in text for term in BAD_TERMS):
                    continue
                if any(norm(term) in text for term in EXTRA_BAD_TERMS):
                    continue
                if any(norm(term) in text for term in REMOVE_TERMS):
                    continue
                category = classify(row)
                if not category:
                    continue
                image = image_for(row)
                url = link_for(row)
                if not image or not url or "shopee" not in url:
                    continue
                itemid = str(row.get("itemid") or title)
                if itemid in seen:
                    continue
                title_key = re.sub(r"[^a-z0-9]+", " ", norm(title)).strip()
                if title_key in seen_titles:
                    continue
                seen.add(itemid)
                seen_titles.add(title_key)
                budget = "10" if price <= 10 else "20" if price <= 20 else "50"
                products.append({
                    "name": title,
                    "label": "Até R$10" if budget == "10" else "R$10 a R$20" if budget == "20" else "Até R$50",
                    "category": category,
                    "price": f"R${price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "desc": desc_for(category, budget),
                    "budget": budget,
                    "image": image,
                    "url": url,
                })
    products.sort(key=lambda product: (
        0 if product["budget"] == "10" else 1 if product["budget"] == "20" else 2,
        CATEGORY_ORDER[product["category"]],
        float(product["price"].replace("R$", "").replace(".", "").replace(",", ".")),
    ))
    return (
        [p for p in products if p["budget"] == "10"][:250]
        + [p for p in products if p["budget"] == "20"][:900]
        + [p for p in products if p["budget"] == "50"][:900]
    )


def update_site(products: list[dict[str, str]]) -> None:
    html = SITE.read_text(encoding="utf-8", errors="replace")
    marker = "const products = "
    start = html.index(marker) + len(marker)
    end = html.index("\n    const productList", start)
    html = html[:start - len(marker)] + marker + json.dumps(products, ensure_ascii=True, indent=6) + ";" + html[end:]
    html = re.sub(
        r'<div class="metric"><strong>\d+</strong><span>ofertas reais do feed Shopee</span></div>',
        f'<div class="metric"><strong>{len(products)}</strong><span>ofertas reais do feed Shopee</span></div>',
        html,
    )
    SITE.write_text(html, encoding="utf-8", newline="\n")
    PUBLISH_SITE.parent.mkdir(parents=True, exist_ok=True)
    PUBLISH_SITE.write_text(html, encoding="utf-8", newline="\n")
    DOCS_SITE.parent.mkdir(parents=True, exist_ok=True)
    DOCS_SITE.write_text(html, encoding="utf-8", newline="\n")


def current_product_count() -> int:
    if not SITE.exists():
        return 0
    html = SITE.read_text(encoding="utf-8", errors="ignore")
    marker = "const products = "
    try:
        start = html.index(marker) + len(marker)
        end = html.index("\n    const productList", start)
        return len(json.loads(html[start:end].rstrip(";")))
    except Exception:
        pass
    match = re.search(r'<div class="metric"><strong>(\d+)</strong><span>ofertas reais do feed Shopee</span></div>', html)
    return int(match.group(1)) if match else 0


def main() -> int:
    urls = feed_urls()
    try:
        feeds = download_feeds(urls) if urls else latest_downloaded_feeds()
    except Exception as error:
        log(f"Falha ao baixar feed por URL: {error}. Usando CSVs em Downloads.")
        feeds = latest_downloaded_feeds()
    if not feeds:
        log("Nenhum feed encontrado.")
        print("Nenhum feed encontrado.", file=sys.stderr)
        return 1

    products = build_products(feeds)
    if not products:
        log("Nenhum produto passou nos filtros.")
        print("Nenhum produto passou nos filtros.", file=sys.stderr)
        return 1

    products = merge_manual_products(products)

    existing_count = current_product_count()
    minimum_count = int(os.environ.get("MIN_SHOPEE_PRODUCTS", "800"))
    if existing_count >= minimum_count and len(products) < minimum_count:
        counts = {"mantido": existing_count, "novo_feed": len(products), "minimo": minimum_count}
        log(f"Feed ignorado por baixo volume: {counts}")
        print(json.dumps(counts, ensure_ascii=False, indent=2))
        return 0

    update_site(products)
    counts = {
        "total": len(products),
        "ate10": sum(p["budget"] == "10" for p in products),
        "r10a20": sum(p["budget"] == "20" for p in products),
        "ate50": sum(p["budget"] == "50" for p in products),
    }
    log(f"Atualizado: {counts} | feeds: {', '.join(path.name for path in feeds)}")
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
