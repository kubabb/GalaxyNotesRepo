"""
ASTRONOMER v2.0 (Semantic Physics Refiner)
Matematyk galaktyki z fizyką semantyczną.
- Czyta pliki .md z vaultu.
- Ekstrahuje [[WikiLinks]].
- Grupuje węzły w ramiona spiralne na podstawie podobieństwa linków.
- Przypisuje współrzędne 3D: ważniejsze notatki bliżej centrum.
- Zapisuje galaxy_data.json w formacie v2.0.
"""
import os
import re
import json
import math
import random
import argparse
from pathlib import Path
from collections import defaultdict

# Ścieżki projektu
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_ENV = PROJECT_ROOT / "config" / ".env"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
OUTPUT_FILE = OUTPUT_DIR / "galaxy_data.json"

LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

# Paleta kolorów dla ramion spirali
ARM_COLORS = [
    "#FF5733", "#33FF57", "#3357FF", "#F333FF",
    "#33FFF5", "#FF33A8", "#FFD433", "#8D33FF",
]

SKIP_DIRS = {".git", "node_modules", "__pycache__"}


def load_env(path: Path) -> dict:
    """Prosty parser pliku .env (KEY=VALUE)."""
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


def get_vault_path(cli_path: str = None) -> Path:
    """Zwraca ścieżkę do vaultu: argument CLI > BRAIN_PATH > TARGET_PATH > domyślna."""
    if cli_path:
        return Path(cli_path)
    env = load_env(CONFIG_ENV)
    for key in ("BRAIN_PATH", "TARGET_PATH"):
        if key in env and env[key]:
            return Path(env[key])
    return Path(r"C:\Users\kubar\OneDrive\Dokumenty\BRAIN")


def should_skip(path_parts) -> bool:
    """Pomija foldery .git, node_modules, __pycache__."""
    return any(part in SKIP_DIRS for part in path_parts)


def extract_links(text: str) -> set:
    """Wyciąga linki Obsidian [[Nazwa]] lub [[Ścieżka|Nazwa]] z tekstu."""
    matches = LINK_PATTERN.findall(text)
    links = set()
    for match in matches:
        clean = match.split("|")[0].strip()
        # Normalizuj separatory ścieżek do nazwy pliku (stem)
        clean = clean.replace("/", "\\")
        link_stem = Path(clean).stem
        if link_stem:
            links.add(link_stem)
    return links


def build_graph(vault_path: Path):
    """
    Buduje graf notatek na podstawie linków Obsidian.
    Zwraca dict: node_name -> {links_out: set(), links_in: set(), file: str}
    """
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault nie istnieje: {vault_path}")

    nodes = {}
    md_files = [
        f for f in vault_path.rglob("*.md")
        if not should_skip(f.parts)
    ]

    # Pierwszy przejazd: rejestracja węzłów
    for md_file in md_files:
        rel = md_file.relative_to(vault_path)
        node_name = md_file.stem
        nodes[node_name] = {
            "file": str(rel),
            "links_out": set(),
            "links_in": set(),
        }

    # Drugi przejazd: ekstrakcja linków
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        links = extract_links(text)
        node_name = md_file.stem
        nodes[node_name]["links_out"] = links

        for link_stem in links:
            if link_stem in nodes:
                nodes[link_stem]["links_in"].add(node_name)

    return nodes


def jaccard(a: set, b: set) -> float:
    """Zwraca współczynnik Jaccarda dla dwóch zbiorów."""
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def compute_spiral_arms(nodes: dict):
    """
    Grupuje węzły w ramiona spiralne na podstawie podobieństwa linków (Jaccard).
    Zwraca (groups_dict, arm_count).
    """
    if not nodes:
        return {}, 0

    # Oblicz degree
    degrees = {name: len(data["links_in"]) + len(data["links_out"]) for name, data in nodes.items()}

    # Ustal liczbę ramion (rozsądna dynamika)
    n = len(nodes)
    arm_count = max(3, min(8, int(math.sqrt(n))))
    if n < arm_count:
        arm_count = max(1, n)

    # Zbiory cech dla każdego węzła (linki przychodzące + wychodzące)
    features = {
        name: nodes[name]["links_out"] | nodes[name]["links_in"]
        for name in nodes
    }

    # Wybierz seed'y (centrówki ramion): top-degree z różnorodnością
    sorted_by_deg = sorted(nodes.keys(), key=lambda x: degrees[x], reverse=True)
    seeds = []
    for name in sorted_by_deg:
        if len(seeds) >= arm_count:
            break
        # Sprawdź różnorodność: akceptuj jeśli Jaccard z istniejącymi seedami < 0.5
        # lub brak seedów
        ok = True
        for s in seeds:
            if jaccard(features[name], features[s]) > 0.5:
                ok = False
                break
        if ok or len(seeds) == 0:
            seeds.append(name)

    # Jeśli seedów za mało, dopełnij kolejnymi top-degree
    for name in sorted_by_deg:
        if len(seeds) >= arm_count:
            break
        if name not in seeds:
            seeds.append(name)

    # Przypisz każdy węzeł do najbliższego seeda (max Jaccard)
    groups = {}
    group_sizes = defaultdict(int)

    for name in nodes:
        if name in seeds:
            g = seeds.index(name)
            groups[name] = g
            group_sizes[g] += 1
            continue

        best_g = 0
        best_sim = -1.0
        for idx, seed in enumerate(seeds):
            sim = jaccard(features[name], features[seed])
            if sim > best_sim:
                best_sim = sim
                best_g = idx

        # Jeśli zero podobieństwa, wyrównaj do najmniejszej grupy
        if best_sim <= 0.0 and group_sizes:
            best_g = min(group_sizes.keys(), key=lambda g: group_sizes[g])
        elif best_sim <= 0.0:
            best_g = 0

        groups[name] = best_g
        group_sizes[best_g] += 1

    return groups, arm_count


def build_edges(nodes: dict):
    """
    Buduje listę krawędzi (edges) między węzłami.
    Zwraca listę dictów: {source, target}.
    """
    edges = []
    seen = set()
    for source, data in nodes.items():
        for target in data["links_out"]:
            if target in nodes:
                key = tuple(sorted([source, target]))
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": source, "target": target})
    return edges


def random_point_in_sphere(radius: float) -> tuple:
    """Generuje losowy punkt wewnątrz sfery o zadanym promieniu (Marsaglia method)."""
    while True:
        x, y, z = random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)
        d2 = x*x + y*y + z*z
        if d2 <= 1:
            r = radius * (d2 ** (1/3))  # uniform volume distribution
            return (x * r, y * r, z * r)


def assign_coordinates(nodes: dict, groups: dict, arm_count: int):
    """
    Przypisuje współrzędne 3D (X, Y, Z) dla każdego węzła.
    UKŁAD WOLUMETRYCZNY – pełna sfera. Gwiazdy rozrzucone w całej objętości,
    nie tylko na płaszczyźnie. Użytkownik jest WŚRÓD nich z każdej strony.
    """
    positions = {}
    degrees = {name: len(data["links_in"]) + len(data["links_out"]) for name, data in nodes.items()}
    n = len(nodes)

    # Klastry jako sfery 3D – rozrzucone w całej objętości
    cluster_count = max(12, min(20, int(n ** 0.45)))
    clusters = []
    for _ in range(cluster_count):
        clusters.append({
            "cx": random.uniform(-5000, 5000),
            "cy": random.uniform(-4000, 4000),
            "cz": random.uniform(-4000, 4000),
            "radius": random.uniform(900, 2200),
        })

    # Supermasywna czarna dziura – centrum galaktyki
    core = {"cx": 0, "cy": 0, "cz": 0, "radius": 1800}
    clusters.append(core)

    for name in nodes:
        degree = degrees[name]
        val = min(max(degree, 1), 10)
        arm_index = groups.get(name, 0) % arm_count if arm_count else 0

        if degree == 0:
            # Osierocone notatki – szeroko poza głównym obszarem
            x, y, z = random_point_in_sphere(7000)
        else:
            # Wybierz klaster deterministycznie
            cluster_idx = hash(name) % len(clusters)
            cluster = clusters[cluster_idx]

            # Promień wewnątrz sfery klastra – ważniejsze bliżej centrum
            max_r = cluster["radius"]
            r = random.uniform(0, max_r) * (1.0 - min(degree, 10) / 14.0)
            dx, dy, dz = random_point_in_sphere(r)

            x = cluster["cx"] + dx
            y = cluster["cy"] + dy
            z = cluster["cz"] + dz

            # Szum 3D
            x += random.uniform(-500, 500)
            y += random.uniform(-500, 500)
            z += random.uniform(-500, 500)

            # Superważne notatki mocniej w centrum galaktyki
            if degree >= 8:
                x *= 0.15
                y *= 0.15
                z *= 0.15

        positions[name] = {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "val": val,
            "color": ARM_COLORS[arm_index % len(ARM_COLORS)],
            "group": f"ramie_{arm_index + 1}",
        }

    return positions


def refine_galaxy(vault_path: Path = None):
    """Główna funkcja agenta – buduje i zapisuje dane galaktyki v2.0."""
    print(f"[ASTRONOMER v2.0] Skanuję vault: {vault_path}")
    nodes_raw = build_graph(vault_path)
    print(f"[ASTRONOMER v2.0] Znaleziono {len(nodes_raw)} notatek.")

    groups, arm_count = compute_spiral_arms(nodes_raw)
    print(f"[ASTRONOMER v2.0] Wyodrębniono {arm_count} ramion spiralnych.")

    edges = build_edges(nodes_raw)
    print(f"[ASTRONOMER v2.0] Znaleziono {len(edges)} krawędzi.")

    positions = assign_coordinates(nodes_raw, groups, arm_count)

    # Przygotuj finalny format nodes
    nodes_out = {}
    for name in nodes_raw:
        nodes_out[name] = positions[name]

    output_data = {
        "nodes": nodes_out,
        "edges": edges,
        "meta": {
            "node_count": len(nodes_out),
            "edge_count": len(edges),
            "spiral_arms": arm_count,
        }
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"[ASTRONOMER v2.0] Zapisano galaxy_data.json w {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Galaxy Mapper v2.0")
    parser.add_argument("--vault", type=str, default=None, help="Ścieżka do vaultu z notatkami .md")
    args = parser.parse_args()

    vault = get_vault_path(args.vault)
    refine_galaxy(vault)
