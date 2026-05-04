"""
ASTRONOMER (Data Refiner)
Matematyk galaktyki. Oblicza „wagę” notatek (im więcej linków prowadzi
do notatki, tym większa i jaśniejsza jest gwiazda).
Przetwarza surowy graf połączeń na współrzędne i przypisuje kolory
na podstawie folderów 01-04.
"""
import re
import json
import math
import random
from pathlib import Path
from collections import defaultdict

# Domyślna ścieżka do vaultu BRAIN
DEFAULT_BRAIN_PATH = Path(r"C:\Users\kubar\OneDrive\Dokumenty\BRAIN")

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output"
OUTPUT_FILE = OUTPUT_DIR / "galaxy_data.json"

# Kolory dla folderów (HEX)
FOLDER_COLORS = {
    "01": "#3B82F6",  # niebieski – Projects
    "02": "#10B981",  # zielony – Library
    "03": "#F59E0B",  # pomarańczowy – Standards
    "04": "#EF4444",  # czerwony – Archive
}
DEFAULT_COLOR = "#9CA3AF"  # szary

LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def extract_links(text: str) -> set:
    """Wyciąga linki Obsidian [[Nazwa]] lub [[Ścieżka|Nazwa]] z tekstu."""
    matches = LINK_PATTERN.findall(text)
    links = set()
    for match in matches:
        # Usuń ewentualny alias
        clean = match.split("|")[0].strip()
        clean = clean.replace("/", "\\")
        links.add(clean)
    return links


def detect_folder_category(relative_path: Path) -> str:
    """Wykrywa kategorię folderu (01-04) na podstawie ścieżki."""
    parts = relative_path.parts
    for part in parts:
        if part.startswith("01_"):
            return "01"
        if part.startswith("02_"):
            return "02"
        if part.startswith("03_"):
            return "03"
        if part.startswith("04_"):
            return "04"
    return "other"


def build_graph(vault_path: Path = DEFAULT_BRAIN_PATH):
    """
    Buduje graf notatek na podstawie linków Obsidian.
    Zwraca dict: nazwa_pliku -> {links, weight, category, color}
    """
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault BRAIN nie istnieje: {vault_path}")

    nodes = {}
    # Zbierz wszystkie pliki .md, pomijając .git/
    md_files = [
        f for f in vault_path.rglob("*.md")
        if ".git" not in f.parts
    ]

    # Pierwszy przejazd: stwórz węzły
    for md_file in md_files:
        rel = md_file.relative_to(vault_path)
        category = detect_folder_category(rel)
        node_name = md_file.stem
        nodes[node_name] = {
            "file": str(rel),
            "links_out": set(),
            "links_in": set(),
            "category": category,
            "color": FOLDER_COLORS.get(category, DEFAULT_COLOR),
        }

    # Drugi przejazd: wypełnij linki
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        links = extract_links(text)
        node_name = md_file.stem
        nodes[node_name]["links_out"] = links

        # Zarejestruj linki przychodzące
        for link in links:
            # Link może być nazwą pliku bez rozszerzenia lub ścieżką
            link_stem = Path(link).stem
            if link_stem in nodes:
                nodes[link_stem]["links_in"].add(node_name)

    # Oblicz wagi (in-degree)
    for name, data in nodes.items():
        data["weight"] = len(data["links_in"])

    return nodes


def build_edges(nodes: dict):
    """
    Buduje listę krawędzi (edges) między węzłami.
    Zwraca listę dictów: {source, target, weight}
    """
    edges = []
    seen = set()
    for source, data in nodes.items():
        for target in data["links_out"]:
            target_stem = Path(target).stem
            if target_stem in nodes:
                # Unikaj duplikatów (A->B i B->A)
                key = tuple(sorted([source, target_stem]))
                if key not in seen:
                    seen.add(key)
                    # Waga krawędzi = suma linków w obie strony
                    weight = 1
                    if source in nodes[target_stem]["links_out"]:
                        weight = 2
                    edges.append({
                        "source": source,
                        "target": target_stem,
                        "weight": weight
                    })
    return edges


def assign_coordinates(nodes: dict):
    """
    Przypisuje współrzędne 3D (X, Y, Z) dla każdego węzła.
    Tworzy galaktykę spiralną z ramionami spiralnymi.
    Pliki gęsto połączone (wysoki degree) tworzą konstelacje w płaszczyznach.
    """
    names = list(nodes.keys())
    n = len(names)
    if n == 0:
        return nodes

    # Oblicz degree (in + out) dla konstelacji
    for name in nodes:
        nodes[name]["degree"] = len(nodes[name]["links_in"]) + len(nodes[name]["links_out"])

    # Posortuj według wagi malejąco – cięższe bliżej centrum
    names.sort(key=lambda x: nodes[x]["weight"], reverse=True)

    positions = {}
    # Parametry galaktyki spiralnej
    spiral_tightness = 0.3  # jak bardzo skręcone są ramiona
    arm_count = 3  # liczba ramion spiralnych
    disk_thickness = 15  # grubosć dysku galaktyki

    for i, name in enumerate(names):
        weight = nodes[name]["weight"]
        degree = nodes[name]["degree"]

        # Promień: ważniejsze bliżej centrum
        base_radius = 20 + i * 25
        if weight > 0:
            base_radius = base_radius / (1 + 0.5 * math.log1p(weight))
        base_radius = max(5, base_radius)

        # Kąt: podstawowy + wkład spiralny
        arm_offset = (hash(name) % arm_count) * (2 * math.pi / arm_count)
        spiral_angle = base_radius * spiral_tightness
        angle = arm_offset + spiral_angle + (i * 0.1)

        # Współrzędne X, Y w płaszczyźnie dysku
        x = base_radius * math.cos(angle)
        y = base_radius * math.sin(angle)

        # Z: grubość dysku + efekt konstelacji dla gęsto połączonych
        # Węzły o wysokim degree dostają bardziej wyraźną Z
        z = random.uniform(-disk_thickness, disk_thickness)
        if degree > 5:
            # Konstelacje: gęsto połączone węzły wyróżnione na osi Z
            z = z * 0.3 + (degree * 2)
        elif degree > 2:
            z = z * 0.6 + (degree * 0.5)

        positions[name] = {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
        }

    # Dodaj współrzędne do nodes
    for name in nodes:
        nodes[name]["x"] = positions.get(name, {}).get("x", 0)
        nodes[name]["y"] = positions.get(name, {}).get("y", 0)
        nodes[name]["z"] = positions.get(name, {}).get("z", 0)
        # Konwertuj sety na listy dla JSON
        nodes[name]["links_out"] = list(nodes[name]["links_out"])
        nodes[name]["links_in"] = list(nodes[name]["links_in"])

    return nodes


def refine_galaxy(vault_path: Path = None):
    """Główna funkcja agenta – buduje i zapisuje dane galaktyki."""
    if vault_path is None:
        vault_path = DEFAULT_BRAIN_PATH

    print(f"[ASTRONOMER] Skanuję vault: {vault_path}")
    nodes = build_graph(vault_path)
    print(f"[ASTRONOMER] Znaleziono {len(nodes)} notatek.")

    edges = build_edges(nodes)
    print(f"[ASTRONOMER] Znaleziono {len(edges)} krawędzi.")

    nodes = assign_coordinates(nodes)

    output_data = {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "vault_path": str(vault_path),
        }
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"[ASTRONOMER] Zapisano galaxy_data.json w {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    refine_galaxy()
