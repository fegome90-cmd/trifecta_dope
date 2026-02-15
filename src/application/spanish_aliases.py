"""Spanish alias detection and expansion for search.

Provides two-pass search:
1. First pass: original query
2. Second pass (if hits=0 and Spanish detected): try aliases

This minimizes false positives while addressing the common Spanish->English gap.
"""

import re
from typing import Dict, List, Tuple


SPANISH_STOPWORDS = {
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "unos",
    "unas",
    "de",
    "del",
    "al",
    "en",
    "por",
    "para",
    "con",
    "sin",
    "que",
    "cual",
    "quien",
    "cuando",
    "donde",
    "como",
    "es",
    "son",
    "fue",
    "fueron",
    "ser",
    "estar",
    "hay",
    "este",
    "esta",
    "estos",
    "estas",
    "ese",
    "esa",
    "esos",
    "esas",
    "mi",
    "tu",
    "su",
    "mis",
    "tus",
    "sus",
    "mi",
    "nuestro",
    "y",
    "o",
    "pero",
    "porque",
    "aunque",
    "si",
    "no",
    "se",
    "le",
    "les",
    "me",
    "te",
    "nos",
    "os",
    "yo",
    "tu",
    "el",
    "ella",
    "nosotros",
    "vosotros",
    "ellos",
    "mas",
    "muy",
    "todo",
    "toda",
    "todos",
    "todas",
    "otro",
    "otra",
    "otros",
    "otras",
    "mismo",
    "misma",
}

SPANISH_CHARS_PATTERN = re.compile(r"[áéíóúñü¿¡]", re.IGNORECASE)

SPANISH_ALIASES: Dict[str, List[str]] = {
    "servicio": ["service"],
    "servicios": ["service", "services"],
    "busqueda": ["search", "query"],
    "búsqueda": ["search", "query"],
    "documento": ["document", "file", "doc"],
    "documentos": ["document", "file", "docs"],
    "configuracion": ["config", "configuration", "setting"],
    "configuración": ["config", "configuration", "setting"],
    "comando": ["command", "cli"],
    "comandos": ["command", "cli", "commands"],
    "ayuda": ["help", "assist"],
    "problema": ["problem", "issue", "bug", "error"],
    "error": ["error", "fail", "exception"],
    "archivo": ["file", "document"],
    "archivos": ["file", "files", "document"],
    "carpeta": ["folder", "directory", "dir"],
    "directorio": ["directory", "folder", "path"],
    "ruta": ["path", "route"],
    "codigo": ["code", "source"],
    "código": ["code", "source"],
    "proyecto": ["project"],
    "aplicacion": ["application", "app"],
    "aplicación": ["application", "app"],
    "interfaz": ["interface", "ui"],
    "usuario": ["user"],
    "datos": ["data"],
    "informacion": ["information", "info"],
    "información": ["information", "info"],
    "resultado": ["result"],
    "resultados": ["results"],
    "ejemplo": ["example"],
    "test": ["test", "testing"],
    "prueba": ["test", "testing"],
    "pruebas": ["test", "tests", "testing"],
    "descripcion": ["description", "desc"],
    "descripción": ["description", "desc"],
}


def detect_spanish(query: str) -> bool:
    """Detect if query contains Spanish indicators.

    Args:
        query: Raw query string

    Returns:
        True if query appears to be Spanish
    """
    if not query:
        return False

    query_lower = query.lower()

    if SPANISH_CHARS_PATTERN.search(query):
        return True

    words = query_lower.split()
    spanish_word_count = sum(1 for w in words if w in SPANISH_STOPWORDS)

    if len(words) >= 2 and spanish_word_count >= 1:
        return True

    for spanish_term in SPANISH_ALIASES:
        if spanish_term in query_lower:
            return True

    return False


def get_spanish_aliases(query: str) -> List[Tuple[str, str]]:
    """Get alias expansions for Spanish terms in query.

    Args:
        query: Normalized query string

    Returns:
        List of (spanish_term, english_expansion) tuples
    """
    if not query:
        return []

    query_lower = query.lower()
    expansions = []

    for spanish_term, english_terms in SPANISH_ALIASES.items():
        if spanish_term in query_lower:
            for eng in english_terms:
                expansions.append((spanish_term, eng))

    return expansions


def expand_with_spanish_aliases(query: str) -> List[str]:
    """Expand query with Spanish aliases.

    Args:
        query: Normalized query string

    Returns:
        List of query variants (original + expanded)
    """
    variants = [query]

    expansions = get_spanish_aliases(query)

    if not expansions:
        return variants

    for spanish, english in expansions:
        new_query = query.lower().replace(spanish, english)
        if new_query not in variants:
            variants.append(new_query)

    return variants
