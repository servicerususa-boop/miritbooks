# -*- coding: utf-8 -*-
"""Static site generator for Miritbooks.com. Run: python3 src/build.py  ->  site/"""
import os, sys, json, html, shutil, re
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from content import *  # noqa

BASE = "https://miritbooks.com"
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "site")
TODAY = "2026-11-19"
SITE = "מירית ספרים"

SITEMAP = []  # (path, lang, alternates dict)
ICON_WA = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4 4h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H9l-5 4v-4H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/></svg>'
ICON_HEART = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>'


def esc(s):
    return html.escape(s, quote=True)


def wa(text):
    return f"https://wa.me/{PHONE_E164}?text={quote(text)}"


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def cover_exists(key):
    return os.path.exists(os.path.join(OUT, "assets", "img", BOOKS[key]["cover"]))


def og_for(key=None):
    if key and cover_exists(key):
        return "/assets/img/" + BOOKS[key]["cover"]
    return "/assets/img/og-default.png"


# ------------------------------------------------------------------ schema
ORG = {
    "@type": "Organization",
    "@id": BASE + "/#org",
    "name": SITE,
    "alternateName": "Miritbooks",
    "url": BASE + "/",
    "contactPoint": [{
        "@type": "ContactPoint",
        "telephone": PHONE_INTL,
        "contactType": "customer service",
        "availableLanguage": ["he", "en"],
        "areaServed": "IL",
    }],
}
PERSON = {
    "@type": "Person",
    "@id": BASE + "/about/#mirit",
    "name": "מירית כחלון",
    "alternateName": "Mirit Kahalon",
    "url": BASE + "/about/",
    "jobTitle": "סופרת",
    "description": "סופרת ישראלית שכותבת פרוזה על נושאים נפוצים שאף אחד לא מדבר עליהם.",
}


def ld(obj):
    if isinstance(obj, dict) and "@context" not in obj:
        obj = {"@context": "https://schema.org", **obj}
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def book_ld(key, lang="he"):
    b = BOOKS[key]
    path = b["path"] if lang == "he" else b["en_path"]
    d = {
        "@type": ["Product", "Book"],
        "@id": BASE + path + "#book",
        "name": b["title"] if lang == "he" else b["en_title"],
        "alternateName": b["en_title"] if lang == "he" else b["title"],
        "url": BASE + path,
        "description": b["blurb"] if lang == "he" else b["en_blurb"],
        "image": BASE + og_for(key),
        "inLanguage": "he",
        "bookFormat": "https://schema.org/Paperback",
        "author": {"@type": "Person", "name": "מירית כחלון", "alternateName": "Mirit Kahalon", "url": BASE + "/about/"},
        "brand": {"@type": "Brand", "name": SITE},
        "offers": {
            "@type": "Offer",
            "url": BASE + path,
            "price": str(b["price"]),
            "priceCurrency": "ILS",
            "availability": "https://schema.org/InStock",
            "itemCondition": "https://schema.org/NewCondition",
            "seller": {"@type": "Organization", "name": SITE, "url": BASE + "/"},
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {"@type": "MonetaryAmount", "value": str(b["shipping"]), "currency": "ILS"},
                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "IL"},
            },
        },
    }
    if key == "bat":
        d["workExample"] = {"@type": "Book", "bookFormat": "https://schema.org/EBook", "inLanguage": "he", "url": EVRIT}
    return d


def bundle_ld():
    return {
        "@type": "Product",
        "@id": BASE + "/bundle/#bundle",
        "name": "מארז שני הספרים עם הקדשה אישית: בת + 102 לייקים",
        "description": BUNDLE["text"],
        "url": BASE + "/bundle/",
        "image": BASE + og_for(),
        "brand": {"@type": "Brand", "name": SITE},
        "offers": {
            "@type": "Offer", "url": BASE + "/bundle/", "price": str(BUNDLE["price"]), "priceCurrency": "ILS",
            "availability": "https://schema.org/InStock", "itemCondition": "https://schema.org/NewCondition",
            "seller": {"@type": "Organization", "name": SITE, "url": BASE + "/"},
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "ILS"},
                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "IL"},
            },
        },
    }


def faq_ld(items):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}


def crumbs_ld(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p} for i, (p, n) in enumerate(items)]}


def post_ld(p):
    return {
        "@type": "BlogPosting",
        "headline": p["title"],
        "description": p["desc"],
        "datePublished": p["date"], "dateModified": p["date"],
        "inLanguage": "he",
        "mainEntityOfPage": BASE + f"/blog/{p['slug']}/",
        "image": BASE + og_for(),
        "author": {"@type": "Organization", "name": SITE, "url": BASE + "/"},
        "publisher": {"@type": "Organization", "name": SITE, "url": BASE + "/"},
    }


# ------------------------------------------------------------------ layout
NAV_HE = [("/store/", "חנות"), ("/blog/", "בלוג"), ("/book-clubs/", "מועדוני קריאה"),
          ("/shipping/", "משלוחים ותשלום"), ("/about/", "על מירית")]
NAV_EN = [("/en/", "Books"), ("/en/books/bat/", "Bat"), ("/en/books/102-likes/", "102 Likes")]


def nav_html(path, lang, en_path=None):
    items = NAV_HE if lang == "he" else NAV_EN
    out = []
    for href, label in items:
        cur = ' aria-current="page"' if href == path else ""
        out.append(f'<a href="{href}"{cur}>{esc(label)}</a>')
    if lang == "he":
        out.append(f'<a class="nav__lang" href="{en_path or "/en/"}" hreflang="en" lang="en">English</a>')
    else:
        out.append('<a class="nav__lang" href="/" hreflang="he" lang="he">עברית</a>')
    return "\n".join(out)


def header(path, lang, en_path=None):
    brand = "מירית כחלון" if lang == "he" else "Mirit Kahalon"
    label = "ניווט ראשי" if lang == "he" else "Main navigation"
    home = "/" if lang == "he" else "/en/"
    return f'''<header class="site-header"><div class="wrap site-header__row">
<a class="brand" href="{home}">{brand}</a>
<nav class="nav" aria-label="{label}">
{nav_html(path, lang, en_path)}
</nav></div></header>'''


def footer(lang):
    if lang == "he":
        return f'''<footer class="site-footer"><div class="wrap">
<div class="site-footer__grid">
<div><h2>{SITE}</h2><p>החנות הרשמית של הסופרת מירית כחלון. שני רומנים בעברית, נשלחים עד הבית, אפשר עם הקדשה אישית.</p>
<p><a href="{wa('שלום מירית, יש לי שאלה')}" rel="noopener">וואטסאפ {PHONE_DISPLAY}</a></p></div>
<div><h2>בחנות</h2><ul>
<li><a href="/books/bat/">בת</a></li><li><a href="/books/102-likes/">102 לייקים</a></li>
<li><a href="/bundle/">מארז במתנה</a></li><li><a href="/book-clubs/">מועדוני קריאה וארגונים</a></li></ul></div>
<div><h2>מידע</h2><ul>
<li><a href="/shipping/">משלוחים ותשלום</a></li><li><a href="/blog/">בלוג</a></li>
<li><a href="/about/">על מירית</a></li><li><a href="/press/">לתקשורת</a></li><li><a href="/en/" hreflang="en" lang="en">English</a></li></ul></div>
</div>
<p class="site-footer__legal">© 2026 מירית כחלון. כל הזכויות שמורות.</p>
</div></footer>'''
    return f'''<footer class="site-footer"><div class="wrap">
<div class="site-footer__grid">
<div><h2>Miritbooks</h2><p>The official store of Israeli author Mirit Kahalon. Two Hebrew novels, shipped from Israel, with optional personal dedication.</p>
<p><a href="{wa('Hello Mirit, I have a question')}" rel="noopener">WhatsApp {PHONE_INTL}</a></p></div>
<div><h2>Books</h2><ul><li><a href="/en/books/bat/">Bat</a></li><li><a href="/en/books/102-likes/">102 Likes</a></li></ul></div>
<div><h2>More</h2><ul><li><a href="/" hreflang="he" lang="he">עברית</a></li><li><a href="/about/" hreflang="he" lang="he">על מירית</a></li></ul></div>
</div>
<p class="site-footer__legal">© 2026 Mirit Kahalon. All rights reserved.</p>
</div></footer>'''


def crumbs_html(items, lang="he"):
    label = "פירורי לחם" if lang == "he" else "Breadcrumb"
    lis = []
    for i, (p, n) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f"<li aria-current=\"page\">{esc(n)}</li>")
        else:
            lis.append(f'<li><a href="{p}">{esc(n)}</a></li>')
    return f'<nav class="crumbs wrap" aria-label="{label}"><ol>{"".join(lis)}</ol></nav>'


def render(path, lang, title, desc, body, schemas=None, og_image=None, alt=None, og_type="website",
           published=None, index=True):
    """Write one page. alt = {"he": path, "en": path} for hreflang pairs."""
    schemas = schemas or []
    url = BASE + path
    og_image = og_image or og_for()
    dirattr = 'lang="he" dir="rtl"' if lang == "he" else 'lang="en" dir="ltr"'
    locale = "he_IL" if lang == "he" else "en_US"
    alts = ""
    if alt:
        for l, p in alt.items():
            alts += f'<link rel="alternate" hreflang="{l}" href="{BASE}{p}">\n'
        alts += f'<link rel="alternate" hreflang="x-default" href="{BASE}{alt.get("he", path)}">\n'
    robots = "" if index else '<meta name="robots" content="noindex">\n'
    skip = "דלגו לתוכן" if lang == "he" else "Skip to content"
    page = f'''<!doctype html>
<html {dirattr}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}<link rel="canonical" href="{url}">
{alts}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:locale" content="{locale}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}{og_image}">
<meta name="theme-color" content="#f2b8c6">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{SITE}" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700&family=Suez+One&display=swap">
<link rel="stylesheet" href="/assets/style.css">
{chr(10).join(ld(s) for s in schemas)}
</head>
<body>
<a class="skip" href="#main">{skip}</a>
{header(path, lang, (alt or {}).get("en"))}
<main id="main">
{body}
</main>
{footer(lang)}
<script src="/assets/app.js" defer></script>
</body>
</html>
'''
    d = os.path.join(OUT, path.strip("/"))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    if index:
        SITEMAP.append((path, lang, alt))


# ------------------------------------------------------------------ blocks
def visual(key, lang="he"):
    b = BOOKS[key]
    if cover_exists(key):
        alt = f"כריכת הספר {b['title']} מאת מירית כחלון" if lang == "he" else f"Cover of {b['en_title']} by Mirit Kahalon"
        from PIL import Image
        w, h = Image.open(os.path.join(OUT, "assets", "img", b["cover"])).size
        return f'<img class="coverimg" src="/assets/img/{b["cover"]}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async">'
    if lang == "he":
        title = '<p class="titlecard__title">בת</p>' if key == "bat" else '<p class="titlecard__title titlecard__title--num">102<br>לייקים</p>'
        sub, by, aria = "רומן", "מירית כחלון", f"כרטיס הספר {b['title']}"
    else:
        title = '<p class="titlecard__title">Bat</p>' if key == "bat" else '<p class="titlecard__title titlecard__title--num">102<br>Likes</p>'
        sub, by, aria = "A novel", "Mirit Kahalon", f"Title card for {b['en_title']}"
    return (f'<div class="titlecard titlecard--{b["card"]}" role="img" aria-label="{esc(aria)}">{title}'
            f'<div><p class="titlecard__sub">{sub}</p><p class="titlecard__by">{by}</p></div></div>')


def product_block(key, h="h3", detail=True):
    b = BOOKS[key]
    title = f'<a href="{b["path"]}">{esc(b["title"])}</a>' if detail else esc(b["title"])
    evrit = f'<a class="btn btn-ghost" href="{EVRIT}" rel="noopener">ספר דיגיטלי ב-e-vrit</a>' if key == "bat" else ""
    note = f'{b["price_note"]}. ' if b["price_note"] else ""
    return f'''<article class="product">
<div class="product__visual">{visual(key)}</div>
<div class="product__info">
<{h}>{title}</{h}>
<p>{esc(b["blurb"])}</p>
<ul class="product__meta"><li>{esc(b["format"])}</li><li>עברית</li></ul>
<p class="price">₪{b["price"]}</p>
<p class="price__note">{note}משלוח ₪{b["shipping"]}. משלוח חינם באשקלון והסביבה.</p>
<div class="actions">
<a class="btn btn-primary" href="{PAYBOX[key]}" rel="noopener">לתשלום ב-PayBox</a>
<a class="btn btn-wa" href="{wa(b["wa"])}" rel="noopener">{ICON_WA}הזמנה בוואטסאפ</a>
{evrit}
</div></div></article>'''


def qr_block(key, lang="he"):
    if not os.path.exists(os.path.join(OUT, "assets", "img", f"qr-{key}.png")):
        return ""
    if lang == "he":
        txt, alt = "סורקים עם הנייד ומשלמים ב-PayBox", "קוד QR לתשלום ב-PayBox"
    else:
        txt, alt = "Scan with your phone to pay with PayBox", "QR code to pay with PayBox"
    return (f'<figure class="qr"><img src="/assets/img/qr-{key}.png" alt="{alt}" width="132" height="132" loading="lazy">'
            f'<figcaption>{txt}</figcaption></figure>')


def bundle_block(h="h2"):
    return f'''<div class="bundle">
<div><{h}>מארז במתנה: שני הספרים עם הקדשה אישית</{h}>
<p class="lead">בת ו-102 לייקים, הקדשה אישית מהסופרת ומשלוח עד הבית. מתנה שאי אפשר למצוא בחנות.</p></div>
<div><p class="price">₪{BUNDLE["price"]}</p><p>כולל משלוח והקדשה אישית</p>
<div class="actions">
<a class="btn btn-light" href="{PAYBOX["bundle"]}" rel="noopener">לתשלום ב-PayBox</a>
<a class="btn btn-ghost-light" href="{wa(BUNDLE["wa"])}" rel="noopener">{ICON_WA}הזמנה בוואטסאפ</a>
</div></div></div>'''


def soon_block():
    return f'''<div class="soon"><div><h3>עוד ספרים בדרך</h3>
<p>רוצים לדעת ראשונים כשיש חדש? כתבו למירית בוואטסאפ.</p></div>
<a class="btn btn-wa" href="{wa("שלום מירית, אשמח לקבל הודעה כשיוצא ספר חדש")}" rel="noopener">{ICON_WA}עדכנו אותי</a></div>'''


def faq_html(items):
    return '<div class="faq">' + "".join(
        f"<details><summary>{esc(q)}</summary><p>{a}</p></details>" for q, a in items) + "</div>"


def posts_list(posts):
    return '<ul class="posts">' + "".join(
        f'<li><time datetime="{p["date"]}">{p["date"][8:]}.{p["date"][5:7]}.{p["date"][:4]}</time>'
        f'<h3><a href="/blog/{p["slug"]}/">{esc(p["title"])}</a></h3><p>{esc(p["desc"])}</p></li>' for p in posts) + "</ul>"


def share_block(title, url, lang="he"):
    if lang == "he":
        return (f'<div class="share"><button class="btn btn-ghost" type="button" data-share data-url="{url}" data-title="{esc(title)}" data-done="הקישור הועתק">שיתוף</button>'
                f'<a class="btn btn-ghost" href="https://wa.me/?text={quote(title + " " + url)}" rel="noopener">שליחה בוואטסאפ</a>'
                f'<span class="share__status" role="status" aria-live="polite" data-share-status></span></div>')
    return (f'<div class="share"><button class="btn btn-ghost" type="button" data-share data-url="{url}" data-title="{esc(title)}" data-done="Link copied">Share</button>'
            f'<a class="btn btn-ghost" href="https://wa.me/?text={quote(title + " " + url)}" rel="noopener">Send on WhatsApp</a>'
            f'<span class="share__status" role="status" aria-live="polite" data-share-status></span></div>')


def page_head(h1, lead=""):
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return f'<section class="page-head"><div class="wrap"><h1>{h1}</h1>{lead_html}</div></section>'


def clubs_teaser():
    return f'''<section class="band band--mist"><div class="wrap bundle">
<div><h2>מועדון קריאה, ארגון או ספרייה?</h2>
<p class="lead">חבילות לקבוצות, מתנות לעובדים ומפגשי סופרת. כמה עותקים שרוצים.</p></div>
<div class="actions"><a class="btn btn-primary" href="/book-clubs/">לחבילות לקבוצות</a>
<a class="btn btn-ghost" href="/blog/book-club-guide-bat/">שאלות לדיון</a></div></div></section>'''


# ------------------------------------------------------------------ Hebrew pages
def build_home():
    faq = FAQ[:5]
    cards = f'<div class="hero__cards" aria-hidden="true">{visual("bat")}{visual("likes")}</div>'
    body = f'''<section class="hero"><div class="wrap hero__grid">
<div class="hero__text">
<h1 class="quote">״אני לא רוצה עוד ילדים.<br>אני רוצה בת!״</h1>
<p class="quote__src">מתוך הרומן בת מאת מירית כחלון</p>
<p class="lead">מירית כחלון כותבת פרוזה על נושאים נפוצים שאף אחד לא מדבר עליהם. שני רומנים בעברית, נשלחים עד הבית, אפשר עם הקדשה אישית.</p>
<div class="actions"><a class="btn btn-primary" href="/books/bat/">להזמנת הספר בת, ₪{BOOKS["bat"]["price"]}</a>
<a class="btn btn-ghost" href="/books/102-likes/">102 לייקים, ₪{BOOKS["likes"]["price"]}</a></div>
</div>
{cards}
</div></section>
<section class="band" id="store"><div class="wrap">
<div class="band__head"><h2>החנות</h2><p>שני רומנים. משלוח עד הבית, ומשלוח חינם באשקלון והסביבה.</p></div>
{product_block("bat")}
{product_block("likes")}
</div></section>
<section class="band band--ink"><div class="wrap">{bundle_block()}</div></section>
<section class="band"><div class="wrap">{soon_block()}</div></section>
{clubs_teaser()}
<section class="band"><div class="wrap">
<div class="band__head"><h2>על מירית כחלון</h2></div>
<div class="prose"><p>מירית כחלון היא סופרת. היא כותבת פרוזה על נושאים נפוצים שאף אחד לא מדבר עליהם. הרומן הראשון שלה, <a href="/books/102-likes/">102 לייקים</a>, ראה אור ב-2018, והרומן <a href="/books/bat/">בת</a> מודפס לפי הזמנה.</p>
<p><a href="/about/">עוד על מירית</a></p></div>
</div></section>
<section class="band band--mist"><div class="wrap">
<div class="band__head"><h2>מהבלוג</h2></div>
{posts_list(POSTS[:3])}
<p style="margin-top:1.5rem"><a href="/blog/">לכל הפוסטים</a></p>
</div></section>
<section class="band"><div class="wrap">
<div class="band__head"><h2>שאלות נפוצות</h2></div>
{faq_html(faq)}
<p style="margin-top:1.5rem"><a href="/shipping/">כל הפרטים על משלוחים ותשלום</a></p>
</div></section>'''
    schemas = [
        {"@type": "WebSite", "@id": BASE + "/#website", "url": BASE + "/", "name": SITE, "inLanguage": "he",
         "publisher": {"@id": BASE + "/#org"}},
        ORG, PERSON, faq_ld(faq),
    ]
    render("/", "he", "מירית כחלון | רומנים בעברית: בת ו-102 לייקים | הזמנה ישירות מהסופרת",
           "החנות הרשמית של הסופרת מירית כחלון. הרומנים בת ו-102 לייקים, משלוח עד הבית, מארז מתנה עם הקדשה אישית ותשלום ב-PayBox.",
           body, schemas, alt={"he": "/", "en": "/en/"})


def build_store():
    body = page_head("החנות", "שני רומנים מאת מירית כחלון. תשלום ב-PayBox או בביט, משלוח עד הבית.") + f'''
<section class="band"><div class="wrap">
{product_block("bat", "h2")}
{product_block("likes", "h2")}
</div></section>
<section class="band band--ink"><div class="wrap">{bundle_block()}</div></section>
<section class="band"><div class="wrap">{soon_block()}
<p style="margin-top:1.5rem"><a href="/shipping/">משלוחים ותשלום</a></p></div></section>'''
    render("/store/", "he", "החנות: ספרים של מירית כחלון | בת, 102 לייקים ומארז מתנה",
           "קנו את הרומנים בת ו-102 לייקים או מארז מתנה עם הקדשה אישית ישירות מהסופרת מירית כחלון. משלוח עד הבית.",
           crumbs_html([("/", "בית"), ("/store/", "חנות")]) + body,
           [crumbs_ld([("/", "בית"), ("/store/", "חנות")]), book_ld("bat"), book_ld("likes"), bundle_ld()])


PRODUCT_COPY = {
    "bat": {
        "h1": "בת: רומן מאת מירית כחלון",
        "title": "בת: רומן מאת מירית כחלון | הזמנה ישירות מהסופרת",
        "desc": "הרומן בת מאת מירית כחלון: כמה אימהות לבנים היו רוצות בת? קסניה לוקחת את זה צעד רחוק מדי. ₪45, משלוח עד הבית, וגם ספר דיגיטלי.",
        "about": f'''<p><strong>{BOOKS["bat"]["quote"]}</strong></p>
<p>{BOOKS["bat"]["blurb"]}</p>
<p>{BOOKS["bat"]["tagline"]} הספר מתאים לקוראות ולקוראים של פרוזה ישראלית עכשווית, למועדוני קריאה, ולמי שמחפשת מתנה שונה.</p>
<p>קראו על הרומן ב<a href="/blog/about-the-novel-bat/">פוסט על הספר</a>, או הורידו <a href="/blog/book-club-guide-bat/">שאלות לדיון במועדון קריאה</a>.</p>''',
        "get": f'''<p>הספר מודפס לפי הזמנה בישראל ונשלח אליכם אחרי התשלום. מחיר השקה: ₪45, ועוד ₪15 משלוח. תושבי אשקלון והסביבה מקבלים משלוח חינם עד הבית. אפשר גם <a href="{EVRIT}" rel="noopener">עותק דיגיטלי ב-e-vrit</a>.</p>''',
    },
    "likes": {
        "h1": "102 לייקים: רומן מאת מירית כחלון",
        "title": "102 לייקים: רומן מאת מירית כחלון | הזמנה ישירות מהסופרת",
        "desc": "הרומן 102 לייקים מאת מירית כחלון: גליה מסוחררת מהלייקים בפייסבוק עד שהיא מבינה שהכול שקר אחד גדול. ₪39, משלוח עד הבית.",
        "about": f'''<p><strong>{BOOKS["likes"]["quote"]}.</strong></p>
<p>{BOOKS["likes"]["blurb"]}</p>
<p>{BOOKS["likes"]["tagline"]} הנושא, ההתמכרות לאישור ברשתות החברתיות, עדיין מוכר לכל מי שגלל פעם בפיד.</p>
<p>קראו עוד ב<a href="/blog/102-likes-social-media-novel/">פוסט על הספר</a>, או הורידו <a href="/blog/book-club-guide-bat/">שאלות לדיון במועדון קריאה</a>.</p>''',
        "get": '''<p>הספר נשלח אליכם ישירות מהסופרת אחרי התשלום: ₪39, ועוד ₪15 משלוח. תושבי אשקלון והסביבה מקבלים משלוח חינם עד הבית. רוצים גם את בת? <a href="/bundle/">מארז שני הספרים עם הקדשה אישית ב-₪79</a>, כולל משלוח.</p>''',
    },
}


def build_product(key):
    b, c = BOOKS[key], PRODUCT_COPY[key]
    counter = (f'<p class="likes" aria-label="102 לייקים">{ICON_HEART}<span data-count-to="102">102</span></p>' if key == "likes" else "")
    evrit = f'<a class="btn btn-ghost" href="{EVRIT}" rel="noopener">ספר דיגיטלי ב-e-vrit</a>' if key == "bat" else ""
    faq = FAQ[:4]
    url = BASE + b["path"]
    body = f'''<section class="band"><div class="wrap product" style="border-top:0">
<div class="product__visual">{visual(key)}</div>
<div class="product__info">
{counter}
<h1>{c["h1"]}</h1>
<p class="lead">{esc(b["blurb"])}</p>
<ul class="product__meta"><li>{esc(b["format"])}</li><li>עברית</li><li>מאת מירית כחלון</li></ul>
<p class="price">₪{b["price"]}</p>
<p class="price__note">{(b["price_note"] + ". ") if b["price_note"] else ""}משלוח ₪{b["shipping"]}. משלוח חינם באשקלון והסביבה.</p>
<div class="actions">
<a class="btn btn-primary" href="{PAYBOX[key]}" rel="noopener">לתשלום ב-PayBox</a>
<a class="btn btn-wa" href="{wa(b["wa"])}" rel="noopener">{ICON_WA}הזמנה בוואטסאפ</a>
{evrit}
</div>
{qr_block(key)}
{share_block(c["h1"], url)}
</div></div></section>
<section class="band band--mist"><div class="wrap prose">
<h2>על הספר</h2>
{c["about"]}
<h2>איך מקבלים את הספר</h2>
{c["get"]}
</div></section>
<section class="band band--ink"><div class="wrap">{bundle_block()}</div></section>
<section class="band"><div class="wrap">
<div class="band__head"><h2>שאלות נפוצות</h2></div>
{faq_html(faq)}
<p style="margin-top:1.5rem"><a href="/shipping/">כל הפרטים על משלוחים ותשלום</a></p>
</div></section>'''
    items = [("/", "בית"), ("/store/", "חנות"), (b["path"], b["title"])]
    render(b["path"], "he", c["title"], c["desc"], crumbs_html(items) + body,
           [crumbs_ld(items), book_ld(key), faq_ld(faq), PERSON], og_image=og_for(key),
           alt={"he": b["path"], "en": b["en_path"]}, og_type="book" if False else "website")


def build_bundle():
    body = page_head("מארז במתנה: בת ו-102 לייקים", "שני הרומנים של מירית כחלון, הקדשה אישית מהסופרת ומשלוח, ב-₪79.") + f'''
<section class="band band--ink"><div class="wrap">{bundle_block("h2")}</div></section>
<section class="band"><div class="wrap prose">
{qr_block("bundle")}
<h2>מה במארז</h2>
<ul><li>הרומן <a href="/books/bat/">בת</a> (מחיר נפרד: ₪45 ועוד ₪15 משלוח)</li>
<li>הרומן <a href="/books/102-likes/">102 לייקים</a> (מחיר נפרד: ₪39 ועוד ₪15 משלוח)</li>
<li>הקדשה אישית מהסופרת</li><li>משלוח עד הבית</li></ul>
<p>קונים בנפרד ₪99 עם משלוח. במארז ₪79.</p>
<h2>איך מוסיפים הקדשה</h2>
<p>אחרי התשלום כותבים למירית בוואטסאפ למי ההקדשה ומה היא אמורה להגיד.</p>
<p>המארז מתאים למתנה לחנוכה, ליום הולדת או לסתם בלי סיבה. קראו גם: <a href="/blog/hanukkah-book-gift-ideas/">ספר במתנה לחנוכה</a>.</p>
<div class="note"><p>בת מודפס לפי הזמנה. מזמינים מתנה לתאריך מסוים? שאלו את מירית בוואטסאפ לפני התשלום.</p></div>
</div></section>'''
    items = [("/", "בית"), ("/store/", "חנות"), ("/bundle/", "מארז במתנה")]
    render("/bundle/", "he", "מארז ספרים במתנה עם הקדשה אישית | בת + 102 לייקים ב-₪79",
           "מארז במתנה: שני הרומנים של מירית כחלון, הקדשה אישית מהסופרת ומשלוח עד הבית ב-₪79.",
           crumbs_html(items) + body, [crumbs_ld(items), bundle_ld()])


def build_clubs():
    msg = wa("שלום מירית, אנחנו מעוניינים בחבילה לקבוצה: ")
    body = page_head("מועדוני קריאה, ארגונים וספריות", "כמה עותקים שרוצים, ואפשר גם מפגש עם הסופרת.") + f'''
<section class="band"><div class="wrap prose">
<h2>חבילת מועדון קריאה</h2>
<p><strong>10 עותקים של 102 לייקים ב-₪250</strong>, כלומר ₪25 לעותק. אפשר להוסיף מפגש עם הסופרת, בזום או פנים אל פנים.</p>
<h2>הרומן בת למועדון</h2>
<p>בת מודפס לפי הזמנה, ולכן מחיר הכמות נקבע בשיחה. כתבו כמה עותקים אתם צריכים ולמתי.</p>
<h2>ארגונים, ועדי עובדים ומתנות</h2>
<p>מ-20 עותקים, עם הקדשה אישית אם רוצים. המחיר לפי הצעה.</p>
<h2>ספריות ומתנ״סים</h2>
<p>מפגש סופרת לקהל, עם עותקים במחיר מיוחד לאירוע. כתבו את מקום האירוע ואת התאריך המשוער.</p>
<div class="actions"><a class="btn btn-wa" href="{msg}" rel="noopener">{ICON_WA}בקשת הצעה בוואטסאפ</a></div>
<h2>הכנה למפגש</h2>
<p>יש <a href="/blog/book-club-guide-bat/">שאלות לדיון בלי ספוילרים</a> לשני הרומנים. אפשר לשלוח אותן לחברות המועדון לפני המפגש.</p>
</div></section>'''
    items = [("/", "בית"), ("/book-clubs/", "מועדוני קריאה")]
    render("/book-clubs/", "he", "מועדוני קריאה, ארגונים וספריות | ספרים של מירית כחלון בכמויות",
           "חבילות לקבוצות: 10 עותקים של 102 לייקים ב-₪250, מתנות לעובדים ומפגש סופרת עם מירית כחלון.",
           crumbs_html(items) + body, [crumbs_ld(items)])


def build_shipping():
    body = page_head("משלוחים ותשלום", "איך מזמינים, כמה זה עולה ומתי מקבלים.") + f'''
<section class="band"><div class="wrap prose">
<dl class="facts">
<dt>משלוח</dt><dd>₪15 להזמנה. משלוח חינם לתושבי אשקלון והסביבה.</dd>
<dt>מארז שני הספרים</dt><dd>₪79, כולל משלוח והקדשה אישית.</dd>
<dt>תשלום</dt><dd>PayBox. לתשלום בביט, כתבו למירית בוואטסאפ.</dd>
<dt>אספקה</dt><dd>אחרי התשלום מירית תאשר איתכם בוואטסאפ מתי הספר יגיע. בת מודפס לפי הזמנה בישראל.</dd>
<dt>הקדשה אישית</dt><dd>כלולה במארז. על ספר בודד, שאלו בוואטסאפ.</dd>
<dt>ספר דיגיטלי</dt><dd>בת זמין ב-<a href="{EVRIT}" rel="noopener">e-vrit</a>.</dd>
<dt>מחוץ לישראל</dt><dd>כתבו למירית בוואטסאפ לקבלת מחיר משלוח.</dd>
</dl>
<div class="actions"><a class="btn btn-wa" href="{wa("שלום מירית, יש לי שאלה על הזמנה")}" rel="noopener">{ICON_WA}שאלה על הזמנה בוואטסאפ</a></div>
<h2>שאלות נפוצות</h2>
</div></section>
<section class="band band--mist"><div class="wrap">{faq_html(FAQ)}</div></section>'''
    items = [("/", "בית"), ("/shipping/", "משלוחים ותשלום")]
    render("/shipping/", "he", "משלוחים ותשלום | ספרים של מירית כחלון",
           "משלוח עד הבית ב-₪15, משלוח חינם באשקלון והסביבה, תשלום ב-PayBox או בביט והקדשה אישית במארז.",
           crumbs_html(items) + body, [crumbs_ld(items), faq_ld(FAQ)])


def build_about():
    body = page_head("על מירית כחלון") + f'''
<section class="band"><div class="wrap prose">
<p class="lead">מירית כחלון היא סופרת. היא כותבת פרוזה על נושאים נפוצים שאף אחד לא מדבר עליהם.</p>
<p>הרומן הראשון שלה, <a href="/books/102-likes/">102 לייקים</a>, ראה אור ב-2018 ומספר על גליה, שמסוחררת מהלייקים בפייסבוק עד שהיא מבינה שהכול זה שקר אחד גדול.</p>
<p>הרומן <a href="/books/bat/">בת</a> שואל כמה אימהות לבנים היו רוצות בת, וקסניה, גיבורת הספר, לוקחת את העניין צעד אחד רחוק מדי.</p>
<p>רוצים להזמין, להזמין סופרת למפגש או לשאול משהו? כתבו למירית בוואטסאפ: <a href="{wa("שלום מירית")}" rel="noopener">{PHONE_DISPLAY}</a>.</p>
<div class="actions"><a class="btn btn-primary" href="/store/">לחנות</a>
<a class="btn btn-ghost" href="/book-clubs/">מפגשי סופרת</a><a class="btn btn-ghost" href="/press/">לתקשורת</a></div>
</div></section>'''
    items = [("/", "בית"), ("/about/", "על מירית")]
    render("/about/", "he", "על מירית כחלון | סופרת, בת ו-102 לייקים",
           "מירית כחלון היא סופרת שכותבת פרוזה על נושאים נפוצים שאף אחד לא מדבר עליהם. מחברת הרומנים בת ו-102 לייקים.",
           crumbs_html(items) + body, [crumbs_ld(items), PERSON])


def build_press():
    body = page_head("לתקשורת ולבלוגרים", "פרטים לכתבות, ראיונות וביקורות.") + f'''
<section class="band"><div class="wrap prose">
<h2>מי היא</h2>
<p>מירית כחלון היא סופרת ישראלית שכותבת פרוזה על נושאים נפוצים שאף אחד לא מדבר עליהם. פרסמה שני רומנים בעברית: <em>102 לייקים</em> (2018) ו<em>בת</em>.</p>
<h2>הספרים</h2>
<ul>
<li><a href="/books/bat/"><strong>בת</strong></a>: {esc(BOOKS["bat"]["blurb"])}</li>
<li><a href="/books/102-likes/"><strong>102 לייקים</strong></a>: {esc(BOOKS["likes"]["blurb"])}</li>
</ul>
<h2>נושאים לראיון</h2>
<ul>
<li>השאלה שרבות לא שואלות בקול: כמה אימהות לבנים היו רוצות בת?</li>
<li>ההתמכרות ללייקים ולאישור ברשתות החברתיות.</li>
<li>איך מוציאים רומן שמודפס לפי הזמנה.</li>
</ul>
<h2>עותק לביקורת ותיאום</h2>
<p>כתבו למירית בוואטסאפ: <a href="{wa("שלום מירית, אני כותב/ת על ספרים ואשמח לעותק לביקורת")}" rel="noopener">{PHONE_DISPLAY}</a>.</p>
</div></section>'''
    items = [("/", "בית"), ("/press/", "לתקשורת")]
    render("/press/", "he", "לתקשורת ובלוגרים | מירית כחלון, סופרת",
           "מידע לעיתונאים ולבלוגרים: ביוגרפיה קצרה של מירית כחלון, תקצירי הרומנים בת ו-102 לייקים, נושאים לראיון ועותק לביקורת.",
           crumbs_html(items) + body, [crumbs_ld(items), PERSON])


def build_blog():
    body = page_head("בלוג", "על הספרים, על הנושאים שהם נוגעים בהם ועל איך מזמינים.") + f'''
<section class="band"><div class="wrap">{posts_list(POSTS)}</div></section>'''
    items = [("/", "בית"), ("/blog/", "בלוג")]
    render("/blog/", "he", "בלוג | מירית כחלון, על הרומנים בת ו-102 לייקים",
           "פוסטים על הרומנים בת ו-102 לייקים, שאלות לדיון במועדוני קריאה, רעיונות למתנה ומדריך הזמנה.",
           crumbs_html(items) + body, [crumbs_ld(items)])
    for p in POSTS:
        url = BASE + f"/blog/{p['slug']}/"
        art = f'''<article><section class="page-head"><div class="wrap"><h1>{esc(p["title"])}</h1>
<p class="muted"><time datetime="{p["date"]}">{p["date"][8:]}.{p["date"][5:7]}.{p["date"][:4]}</time></p></div></section>
<section class="band"><div class="wrap prose">
{p["body"]}
{share_block(p["title"], url)}
<div class="actions"><a class="btn btn-primary" href="/store/">לחנות</a><a class="btn btn-ghost" href="/blog/">עוד פוסטים</a></div>
</div></section></article>'''
        its = [("/", "בית"), ("/blog/", "בלוג"), (f"/blog/{p['slug']}/", p["title"])]
        render(f"/blog/{p['slug']}/", "he", p["title"] + " | מירית כחלון", p["desc"],
               crumbs_html(its) + art, [crumbs_ld(its), post_ld(p)], og_type="article", published=p["date"])


def build_404():
    body = f'''<section class="band"><div class="wrap prose"><h1>העמוד לא נמצא</h1>
<p>הקישור שגוי או שהעמוד הועבר. אפשר לחזור ל<a href="/">עמוד הבית</a> או ל<a href="/store/">חנות</a>.</p></div></section>'''
    render("/404/", "he", "העמוד לא נמצא | מירית ספרים", "העמוד לא נמצא.", body, index=False)
    shutil.move(os.path.join(OUT, "404", "index.html"), os.path.join(OUT, "404.html"))
    os.rmdir(os.path.join(OUT, "404"))


# ------------------------------------------------------------------ English pages
EN_FAQ = [
    ("How do I order?", "Press the PayBox button next to the book (Israeli buyers), or message Mirit on WhatsApp. The book ships after payment."),
    ("Do you ship outside Israel?", "Message Mirit on WhatsApp for a shipping quote."),
    ("Are the books in English?", "No. Both novels are in Hebrew."),
    ("Is there an ebook?", "Bat is available as a Hebrew ebook on e-vrit."),
    ("Can I get a personal dedication?", "The two-book bundle includes one. Ask on WhatsApp about a dedication on a single book."),
]


def en_product(key):
    b = BOOKS[key]
    evrit = f'<a class="btn btn-ghost" href="{EVRIT}" rel="noopener">Hebrew ebook on e-vrit</a>' if key == "bat" else ""
    return f'''<article class="product">
<div class="product__visual">{visual(key, "en")}</div>
<div class="product__info">
<h2><a href="{b["en_path"]}">{esc(b["en_title"])}</a></h2>
<p>{esc(b["en_blurb"])}</p>
<ul class="product__meta"><li>Novel in Hebrew</li><li>Paperback</li></ul>
<p class="price">₪{b["price"]}</p>
<p class="price__note">Shipping ₪{b["shipping"]} within Israel.</p>
<div class="actions">
<a class="btn btn-primary" href="{PAYBOX[key]}" rel="noopener">Pay with PayBox</a>
<a class="btn btn-wa" href="{wa(b["en_title"] + ": Hello Mirit, I would like to order this book")}" rel="noopener">{ICON_WA}Order on WhatsApp</a>
{evrit}
</div></div></article>'''


def en_faq(items):
    return '<div class="faq">' + "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in items) + "</div>"


def build_en_home():
    body = f'''<section class="hero"><div class="wrap hero__grid">
<div class="hero__text">
<h1 class="quote" style="font-size:clamp(2.4rem,7vw,4.8rem)">Two Hebrew novels, straight from the author.</h1>
<p class="lead">Mirit Kahalon writes prose about common subjects no one talks about. Order <em>Bat</em> or <em>102 Likes</em>, shipped from Israel, with an optional personal dedication.</p>
<div class="actions"><a class="btn btn-primary" href="/en/books/bat/">Bat, ₪{BOOKS["bat"]["price"]}</a>
<a class="btn btn-ghost" href="/en/books/102-likes/">102 Likes, ₪{BOOKS["likes"]["price"]}</a></div></div>
<div class="hero__cards" aria-hidden="true">{visual("bat", "en")}{visual("likes", "en")}</div>
</div></section>
<section class="band"><div class="wrap">
<div class="band__head"><h2>The books</h2></div>
{en_product("bat")}
{en_product("likes")}
</div></section>
<section class="band band--ink"><div class="wrap bundle">
<div><h2>Gift bundle: both novels, personally dedicated</h2><p class="lead">Both books, a personal dedication from the author and shipping within Israel.</p></div>
<div><p class="price">₪{BUNDLE["price"]}</p><div class="actions">
<a class="btn btn-light" href="{PAYBOX["bundle"]}" rel="noopener">Pay with PayBox</a>
<a class="btn btn-ghost-light" href="{wa("Hello Mirit, I would like the two-book bundle with a dedication")}" rel="noopener">{ICON_WA}Order on WhatsApp</a></div></div></div></section>
<section class="band"><div class="wrap">
<div class="band__head"><h2>About Mirit Kahalon</h2></div>
<div class="prose"><p>Mirit Kahalon is an Israeli author who writes prose about common subjects no one talks about. Her first novel, <em>102 Likes</em>, came out in 2018. <em>Bat</em> (Hebrew for "daughter") is printed on demand in Israel.</p>
<p>More books are on the way. Message her on WhatsApp to hear first.</p></div>
</div></section>
<section class="band band--mist"><div class="wrap">
<div class="band__head"><h2>Questions</h2></div>
{en_faq(EN_FAQ)}
<div class="actions"><a class="btn btn-wa" href="{wa("Hello Mirit, I have a question")}" rel="noopener">{ICON_WA}Ask on WhatsApp</a></div>
</div></section>'''
    schemas = [{"@type": "WebSite", "@id": BASE + "/en/#website", "url": BASE + "/en/", "name": "Miritbooks", "inLanguage": "en"},
               ORG, PERSON, faq_ld(EN_FAQ)]
    render("/en/", "en", EN_HOME_TITLE, EN_HOME_DESC, body, schemas, alt={"he": "/", "en": "/en/"})


def build_en_product(key):
    b = BOOKS[key]
    evrit = f'<a class="btn btn-ghost" href="{EVRIT}" rel="noopener">Hebrew ebook on e-vrit</a>' if key == "bat" else ""
    counter = (f'<p class="likes" aria-label="102 likes">{ICON_HEART}<span data-count-to="102">102</span></p>' if key == "likes" else "")
    url = BASE + b["en_path"]
    about = ("Bat means \"daughter\" in Hebrew. " if key == "bat" else "") + b["en_blurb"] + (
        " The novel is written in Hebrew." )
    body = f'''<section class="band"><div class="wrap product" style="border-top:0">
<div class="product__visual">{visual(key, "en")}</div>
<div class="product__info">
{counter}
<h1>{esc(b["en_title"])}: a novel by Mirit Kahalon</h1>
<p class="lead">{esc(b["en_blurb"])}</p>
<ul class="product__meta"><li>Novel in Hebrew</li><li>Paperback</li><li>By Mirit Kahalon</li></ul>
<p class="price">₪{b["price"]}</p>
<p class="price__note">Shipping ₪{b["shipping"]} within Israel. Abroad: message Mirit for a quote.</p>
<div class="actions">
<a class="btn btn-primary" href="{PAYBOX[key]}" rel="noopener">Pay with PayBox</a>
<a class="btn btn-wa" href="{wa(b["en_title"] + ": Hello Mirit, I would like to order this book")}" rel="noopener">{ICON_WA}Order on WhatsApp</a>
{evrit}
</div>
{qr_block(key, "en")}
{share_block(b["en_title"], url, "en")}
</div></div></section>
<section class="band band--mist"><div class="wrap prose"><h2>About the book</h2><p>{esc(about)}</p>
<p>Prefer Hebrew? <a href="{b["path"]}" hreflang="he" lang="he">לעמוד בעברית</a>.</p></div></section>
<section class="band"><div class="wrap"><div class="band__head"><h2>Questions</h2></div>{en_faq(EN_FAQ)}</div></section>'''
    items = [("/en/", "Home"), (b["en_path"], b["en_title"])]
    render(b["en_path"], "en", f'{b["en_title"]}: a Hebrew novel by Mirit Kahalon | Buy from the author',
           f'{b["en_blurb"]} Hebrew novel by Mirit Kahalon, ₪{b["price"]}, shipped from Israel.',
           crumbs_html(items, "en") + body, [crumbs_ld(items), book_ld(key, "en"), faq_ld(EN_FAQ), PERSON],
           og_image=og_for(key), alt={"he": b["path"], "en": b["en_path"]})


# ------------------------------------------------------------------ site files
def md_from_html(s):
    s = re.sub(r"<h2>(.*?)</h2>", r"\n## \1\n", s)
    s = re.sub(r"<li>(.*?)</li>", r"- \1\n", s)
    s = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', lambda m: f'[{m.group(2)}]({m.group(1) if m.group(1).startswith("http") else BASE + m.group(1)})', s)
    s = re.sub(r"</p>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(re.sub(r"\n{3,}", "\n\n", s)).strip()


def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full) or OUT, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def build_files():
    # robots.txt: open to search and AI crawlers
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
            "Google-Extended", "Applebot-Extended", "Bingbot"]
    robots = "User-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
    robots += f"Sitemap: {BASE}/sitemap.xml\n"
    write("robots.txt", robots)

    # sitemap.xml with hreflang pairs
    urls = []
    for path, lang, alt in SITEMAP:
        x = f"<url><loc>{BASE}{path}</loc><lastmod>{TODAY}</lastmod>"
        if alt:
            for l, p in alt.items():
                x += f'<xhtml:link rel="alternate" hreflang="{l}" href="{BASE}{p}"/>'
            x += f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{alt["he"]}"/>'
        urls.append(x + "</url>")
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
          + "\n".join(urls) + "\n</urlset>\n")

    # llms.txt + llms-full.txt (AI visibility)
    b, l = BOOKS["bat"], BOOKS["likes"]
    llms = f"""# מירית ספרים (Miritbooks)

> The official store of Israeli author Mirit Kahalon (מירית כחלון). Two Hebrew novels, "Bat" (בת) and "102 Likes" (102 לייקים), sold directly by the author with shipping from Israel and optional personal dedication. Site language: Hebrew, with English pages for each book.

## Books
- [בת / Bat]({BASE}{b["path"]}): {b["blurb"]} ₪{b["price"]} + ₪{b["shipping"]} shipping. Printed on demand in Israel; Hebrew ebook on e-vrit.
- [102 לייקים / 102 Likes]({BASE}{l["path"]}): {l["blurb"]} ₪{l["price"]} + ₪{l["shipping"]} shipping. First published 2018.
- [Gift bundle / מארז במתנה]({BASE}/bundle/): both novels, personal dedication and shipping, ₪{BUNDLE["price"]}.

## Ordering and policies
- [Shipping and payment / משלוחים ותשלום]({BASE}/shipping/): ₪15 shipping, free in Ashkelon and surrounding area, payment by PayBox or Bit, orders confirmed on WhatsApp.
- [Book clubs, organizations, libraries]({BASE}/book-clubs/): group packs and author meetings.

## Reading and discussion
""" + "".join(f"- [{p['title']}]({BASE}/blog/{p['slug']}/): {p['desc']}\n" for p in POSTS) + f"""
## About and press
- [About Mirit Kahalon]({BASE}/about/)
- [Press and bloggers]({BASE}/press/)
- [English home]({BASE}/en/)

## Contact
WhatsApp {PHONE_INTL} (Hebrew and English)
"""
    write("llms.txt", llms)
    full = llms + "\n---\n\n# Full text of key pages\n\n"
    full += f"## {b['title']}\n\n{b['quote']}\n\n{b['blurb']}\n\n{b['tagline']}\n\n"
    full += f"## {l['title']}\n\n{l['quote']}\n\n{l['blurb']}\n\n{l['tagline']}\n\n"
    full += "## FAQ\n\n" + "".join(f"**{q}**\n{strip_tags(a)}\n\n" for q, a in FAQ)
    for p in POSTS:
        full += f"## {p['title']}\n\n{md_from_html(p['body'])}\n\n"
    write("llms-full.txt", full)

    # RSS
    items = "".join(
        f"<item><title>{esc(p['title'])}</title><link>{BASE}/blog/{p['slug']}/</link><guid>{BASE}/blog/{p['slug']}/</guid>"
        f"<pubDate>Thu, 19 Nov 2026 12:00:00 +0200</pubDate><description>{esc(p['desc'])}</description></item>" for p in POSTS)
    write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE}</title><link>{BASE}/</link>'
          f'<description>פוסטים על הרומנים בת ו-102 לייקים מאת מירית כחלון</description><language>he</language>{items}</channel></rss>\n')

    write("site.webmanifest", json.dumps({"name": SITE, "short_name": "מירית ספרים", "lang": "he", "dir": "rtl", "start_url": "/",
                                          "display": "browser", "theme_color": "#f2b8c6", "background_color": "#fff6f8",
                                          "icons": [{"src": "/assets/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]},
                                         ensure_ascii=False, indent=2))
    write("assets/favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="#f2b8c6"/>'
          '<path fill="#b3264f" d="M32 49l-3.2-2.9C19 37.3 13 32 13 25.4 13 20.2 17 16 22.100 16c3.900 0 7.600 2 9.900 5 2.300-3 6-5 9.900-5C47 16 51 20.200 51 25.400c0 6.600-6 11.900-15.800 20.700L32 49z"/></svg>\n')
    write("CNAME", "miritbooks.com\n")
    write(".nojekyll", "")
    shutil.copy(os.path.join(HERE, "style.css"), os.path.join(OUT, "assets", "style.css"))
    shutil.copy(os.path.join(HERE, "app.js"), os.path.join(OUT, "assets", "app.js"))


def main():
    # keep assets/img (real covers, og image); rebuild everything else
    keep = os.path.join(OUT, "assets", "img")
    tmp = None
    if os.path.isdir(keep):
        tmp = os.path.join(ROOT, ".img_keep")
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        shutil.move(keep, tmp)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"))
    if tmp:
        shutil.move(tmp, keep)
    build_home(); build_store(); build_product("bat"); build_product("likes"); build_bundle(); build_clubs()
    build_shipping(); build_about(); build_press(); build_blog(); build_404()
    build_en_home(); build_en_product("bat"); build_en_product("likes")
    build_files()
    print("pages:", len(SITEMAP))


if __name__ == "__main__":
    main()
