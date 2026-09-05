from datetime import datetime, timezone
from pathlib import Path
import calendar

import feedparser
import requests
from feedgen.feed import FeedGenerator


SOURCE_RSS = (
    "https://www.rigel.com/"
    "investors/news-events/press-releases/rss"
)

NEWS_PAGE = (
    "https://www.rigel.com/"
    "investors/news-events/press-releases"
)

GITHUB_RSS = (
    "https://raw.githubusercontent.com/"
    "plis2100/rss-rigel/main/docs/feed.xml"
)

OUTPUT_FILE = Path("docs/feed.xml")

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


def convertir_fecha(entrada):
    fecha_estructurada = (
        entrada.get("published_parsed")
        or entrada.get("updated_parsed")
    )

    if not fecha_estructurada:
        return None

    segundos = calendar.timegm(fecha_estructurada)

    return datetime.fromtimestamp(
        segundos,
        tz=timezone.utc,
    )


def descargar_noticias():
    print(f"Descargando RSS oficial: {SOURCE_RSS}")

    respuesta = requests.get(
        SOURCE_RSS,
        headers=HEADERS,
        timeout=60,
        allow_redirects=True,
    )

    print(f"Código HTTP recibido: {respuesta.status_code}")
    print(f"Dirección final: {respuesta.url}")

    respuesta.raise_for_status()

    contenido = respuesta.content

    if not contenido:
        raise RuntimeError(
            "La RSS oficial de Rigel está vacía."
        )

    original = feedparser.parse(contenido)

    if not original.entries:
        raise RuntimeError(
            "La fuente oficial no contiene comunicados."
        )

    noticias = []

    for entrada in original.entries:
        titulo = entrada.get("title", "").strip()
        enlace = entrada.get("link", "").strip()

        if not titulo or not enlace:
            continue

        descripcion = (
            entrada.get("summary")
            or entrada.get("description")
            or ""
        ).strip()

        identificador = (
            entrada.get("id")
            or entrada.get("guid")
            or enlace
        )

        noticias.append({
            "titulo": titulo,
            "enlace": enlace,
            "descripcion": descripcion,
            "identificador": identificador,
            "fecha": convertir_fecha(entrada),
        })

    if not noticias:
        raise RuntimeError(
            "No se encontraron comunicados válidos de Rigel."
        )

    fecha_antigua = datetime(
        1970,
        1,
        1,
        tzinfo=timezone.utc,
    )

    noticias.sort(
        key=lambda noticia: (
            noticia["fecha"] or fecha_antigua
        ),
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
    feed.lastBuildDate(datetime.now(timezone.utc))

    feed.link(
        href=NEWS_PAGE,
        rel="alternate",
    )

    feed.link(
        href=GITHUB_RSS,
        rel="self",
        type="application/rss+xml",
    )

    for noticia in noticias[:100]:
        entrada = feed.add_entry()

        entrada.id(str(noticia["identificador"]))
        entrada.title(noticia["titulo"])
        entrada.link(href=noticia["enlace"])

        entrada.description(
            noticia["descripcion"]
            or (
                "Read the complete announcement from "
                f"Rigel Pharmaceuticals: {noticia['titulo']}"
            )
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

    if not OUTPUT_FILE.exists():
        raise RuntimeError(
            "No se pudo crear docs/feed.xml"
        )

    print(f"RSS creada: {OUTPUT_FILE}")
    print(f"Tamaño: {OUTPUT_FILE.stat().st_size} bytes")


def main():
    noticias = descargar_noticias()
    crear_rss(noticias)


if __name__ == "__main__":
    main()
