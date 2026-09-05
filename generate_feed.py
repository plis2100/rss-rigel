from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from dateutil import parser as date_parser
from feedgen.feed import FeedGenerator


SOURCE_RSS = "https://www.rigel.com/rss/news-releases.xml"
NEWS_PAGE = "https://www.rigel.com/investors/news-events/press-releases"
OUTPUT_FILE = Path("docs/feed.xml")

GITHUB_RSS = (
    "https://raw.githubusercontent.com/"
    "plis2100/rss-rigel/main/docs/feed.xml"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "application/rss+xml, application/xml, "
        "text/xml;q=0.9, */*;q=0.8"
    ),
}


def descargar_rss():
    respuesta = requests.get(
        SOURCE_RSS,
        headers=HEADERS,
        timeout=60,
    )
    respuesta.raise_for_status()

    contenido = respuesta.content

    if not contenido:
        raise RuntimeError(
            "La RSS oficial de Rigel está vacía. "
            "La RSS anterior no será eliminada."
        )

    return contenido


def convertir_fecha(entrada):
    posibles_fechas = [
        entrada.get("published"),
        entrada.get("updated"),
        entrada.get("pubDate"),
    ]

    for fecha_texto in posibles_fechas:
        if not fecha_texto:
            continue

        try:
            fecha = date_parser.parse(fecha_texto)

            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)

            return fecha

        except (ValueError, TypeError, OverflowError):
            continue

    return None


def obtener_descripcion(entrada):
    descripcion = (
        entrada.get("summary")
        or entrada.get("description")
        or ""
    )

    if not descripcion and entrada.get("content"):
        descripcion = entrada["content"][0].get("value", "")

    return descripcion.strip()


def obtener_noticias():
    contenido = descargar_rss()
    feed_original = feedparser.parse(contenido)

    if feed_original.bozo and not feed_original.entries:
        raise RuntimeError(
            f"Error interpretando la RSS de Rigel: "
            f"{feed_original.bozo_exception}"
        )

    noticias = []

    for entrada in feed_original.entries:
        titulo = entrada.get("title", "").strip()
        enlace = entrada.get("link", "").strip()

        if not titulo or not enlace:
            continue

        noticias.append({
            "titulo": titulo,
            "enlace": enlace,
            "descripcion": obtener_descripcion(entrada),
            "fecha": convertir_fecha(entrada),
            "identificador": (
                entrada.get("id")
                or entrada.get("guid")
                or enlace
            ),
        })

    if not noticias:
        raise RuntimeError(
            "No se encontraron comunicados en la RSS de Rigel. "
            "La RSS anterior no será eliminada."
        )

    fecha_antigua = datetime(
        1970,
        1,
        1,
        tzinfo=timezone.utc,
    )

    noticias.sort(
        key=lambda noticia: noticia["fecha"] or fecha_antigua,
        reverse=True,
    )

    print(f"Comunicados encontrados: {len(noticias)}")

    return noticias


def crear_rss(noticias):
    feed = FeedGenerator()

    feed.id(GITHUB_RSS)
    feed.title("Rigel Pharmaceuticals – News Releases")
    feed.description(
        "Official news releases from Rigel Pharmaceuticals"
    )
    feed.language("en-US")

    feed.link(
        href=NEWS_PAGE,
        rel="alternate",
    )

    feed.link(
        href=GITHUB_RSS,
        rel="self",
        type="application/rss+xml",
    )

    feed.lastBuildDate(datetime.now(timezone.utc))

    for noticia in noticias[:100]:
        entrada = feed.add_entry()

        entrada.id(noticia["identificador"])
        entrada.title(noticia["titulo"])
        entrada.link(href=noticia["enlace"])

        entrada.description(
            noticia["descripcion"]
            or f"Read the complete Rigel announcement: {noticia['titulo']}"
        )

        if noticia["fecha"]:
            entrada.pubDate(noticia["fecha"])

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    feed.rss_file(
        str(OUTPUT_FILE),
        pretty=True,
        encoding="UTF-8",
    )

    print(f"RSS creada correctamente: {OUTPUT_FILE}")


if __name__ == "__main__":
    noticias_obtenidas = obtener_noticias()
    crear_rss(noticias_obtenidas)
