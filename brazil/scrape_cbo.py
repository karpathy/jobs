"""
Scrape CBO (Classificação Brasileira de Ocupações) data.

Step 1: Download CSV files from gov.br (hierarchy: grande grupo, subgrupo, família, ocupação)
Step 2: Scrape occupation descriptions from ocupacoes.com.br (one per família)

Usage:
    uv run python brazil/scrape_cbo.py                  # download CSVs + scrape descriptions
    uv run python brazil/scrape_cbo.py --csv-only       # just download the CSVs
    uv run python brazil/scrape_cbo.py --desc-only      # just scrape descriptions (needs CSVs first)
    uv run python brazil/scrape_cbo.py --force           # re-scrape even if cached
    uv run python brazil/scrape_cbo.py --start 0 --end 5 # scrape descriptions for families 0-4
"""

import argparse
import csv
import json
import os

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIR = "brazil/data"
PAGES_DIR = "brazil/pages"

CBO_CSV_BASE = "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/downloads"
CBO_CSV_FILES = {
    "grande_grupo": "cbo2002-grande-grupo.csv",
    "subgrupo_principal": "cbo2002-subgrupo-principal.csv",
    "subgrupo": "cbo2002-subgrupo.csv",
    "familia": "cbo2002-familia.csv",
    "ocupacao": "cbo2002-ocupacao.csv",
    "sinonimo": "cbo2002-sinonimo.csv",
    "perfil_ocupacional": "cbo2002-perfilocupacional.csv",
}

# ---------------------------------------------------------------------------
# Step 1: Download CBO CSV files
# ---------------------------------------------------------------------------
def download_csvs(force: bool = False):
    """Download all CBO classification CSVs from gov.br."""
    os.makedirs(DATA_DIR, exist_ok=True)

    client = httpx.Client(follow_redirects=True, timeout=30)

    for name, filename in CBO_CSV_FILES.items():
        out_path = os.path.join(DATA_DIR, filename)
        if not force and os.path.exists(out_path):
            print(f"  CACHED {filename}")
            continue

        url = f"{CBO_CSV_BASE}/{filename}"
        print(f"  Downloading {filename}...", end=" ", flush=True)
        try:
            resp = client.get(url)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"OK ({len(resp.content):,} bytes)")
        except Exception as e:
            print(f"ERROR: {e}")

    client.close()


# ---------------------------------------------------------------------------
# Step 2: Parse familia CSV and build occupation list
# ---------------------------------------------------------------------------
def load_familias() -> list[dict]:
    """Load CBO family codes and titles from downloaded CSV."""
    familia_path = os.path.join(DATA_DIR, "cbo2002-familia.csv")
    if not os.path.exists(familia_path):
        raise FileNotFoundError(f"{familia_path} not found. Run with --csv-only first.")

    # Load grande grupo and subgrupo for hierarchy
    ENC = "latin-1"  # gov.br CSVs are ISO-8859-1

    gg_map = {}
    gg_path = os.path.join(DATA_DIR, "cbo2002-grande-grupo.csv")
    if os.path.exists(gg_path):
        with open(gg_path, encoding=ENC) as f:
            for row in csv.DictReader(f, delimiter=";"):
                gg_map[row["CODIGO"]] = row["TITULO"]

    sgp_map = {}
    sgp_path = os.path.join(DATA_DIR, "cbo2002-subgrupo-principal.csv")
    if os.path.exists(sgp_path):
        with open(sgp_path, encoding=ENC) as f:
            for row in csv.DictReader(f, delimiter=";"):
                sgp_map[row["CODIGO"]] = row["TITULO"]

    sg_map = {}
    sg_path = os.path.join(DATA_DIR, "cbo2002-subgrupo.csv")
    if os.path.exists(sg_path):
        with open(sg_path, encoding=ENC) as f:
            for row in csv.DictReader(f, delimiter=";"):
                sg_map[row["CODIGO"]] = row["TITULO"]

    # Load activities from perfil ocupacional (grouped by family)
    atividades_por_familia = {}
    areas_por_familia = {}
    perfil_path = os.path.join(DATA_DIR, "cbo2002-perfilocupacional.csv")
    if os.path.exists(perfil_path):
        with open(perfil_path, encoding=ENC) as f:
            for row in csv.DictReader(f, delimiter=";"):
                fam_code = row["COD_FAMILIA"]
                area = row["NOME_GRANDE_AREA"].strip()
                atividade = row["NOME_ATIVIDADE"].strip()
                if fam_code not in areas_por_familia:
                    areas_por_familia[fam_code] = set()
                areas_por_familia[fam_code].add(area)
                if fam_code not in atividades_por_familia:
                    atividades_por_familia[fam_code] = []
                atividades_por_familia[fam_code].append({
                    "area": area,
                    "atividade": atividade,
                })

    familias = []
    with open(familia_path, encoding=ENC) as f:
        for row in csv.DictReader(f, delimiter=";"):
            codigo = row["CODIGO"].strip()
            titulo = row["TITULO"].strip()

            # Derive hierarchy from code
            gg_code = codigo[0]
            sgp_code = codigo[:2]
            sg_code = codigo[:3]

            slug = f"{codigo}-{slugify(titulo)}"

            # Get activities grouped by area
            areas = sorted(areas_por_familia.get(codigo, set()))
            atividades = atividades_por_familia.get(codigo, [])

            familias.append({
                "codigo": codigo,
                "titulo": titulo,
                "slug": slug,
                "grande_grupo_codigo": gg_code,
                "grande_grupo": gg_map.get(gg_code, "").strip(),
                "subgrupo_principal_codigo": sgp_code,
                "subgrupo_principal": sgp_map.get(sgp_code, "").strip(),
                "subgrupo_codigo": sg_code,
                "subgrupo": sg_map.get(sg_code, "").strip(),
                "areas_de_atividade": areas,
                "atividades": atividades,
            })

    return familias


def slugify(text: str) -> str:
    """Convert a title to a URL-safe slug."""
    import unicodedata
    # Normalize unicode, strip accents
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace non-alphanumeric with hyphens
    slug = ""
    for ch in ascii_text.lower():
        if ch.isalnum():
            slug += ch
        elif slug and slug[-1] != "-":
            slug += "-"
    return slug.strip("-")


# ---------------------------------------------------------------------------
# Step 3: Scrape descriptions from ocupacoes.com.br
# ---------------------------------------------------------------------------
def generate_pages(familias: list[dict], start: int, end: int, force: bool):
    """Generate markdown description pages from CBO perfil data."""
    os.makedirs(PAGES_DIR, exist_ok=True)

    # Also load the ocupacao CSV to get sub-occupation titles per family
    occ_by_family: dict[str, list[str]] = {}
    occ_path = os.path.join(DATA_DIR, "cbo2002-ocupacao.csv")
    if os.path.exists(occ_path):
        with open(occ_path, encoding="latin-1") as f:
            for row in csv.DictReader(f, delimiter=";"):
                code = row["CODIGO"].strip()
                title = row["TITULO"].strip()
                fam_code = code[:4]
                if fam_code not in occ_by_family:
                    occ_by_family[fam_code] = []
                occ_by_family[fam_code].append(f"{code} - {title}")

    subset = familias[start:end]
    generated = 0
    cached = 0

    for i, fam in enumerate(subset, start=start):
        md_path = os.path.join(PAGES_DIR, f"{fam['slug']}.md")
        if not force and os.path.exists(md_path):
            cached += 1
            continue

        lines = []
        lines.append(f"# {fam['titulo']}")
        lines.append(f"**Código CBO:** {fam['codigo']}")
        lines.append(f"**Grande Grupo:** {fam['grande_grupo']}")
        lines.append(f"**Subgrupo Principal:** {fam['subgrupo_principal']}")
        lines.append(f"**Subgrupo:** {fam['subgrupo']}")
        lines.append("")

        # Sub-occupations
        sub_occs = occ_by_family.get(fam["codigo"], [])
        if sub_occs:
            lines.append("## Ocupações nesta família")
            for occ in sub_occs:
                lines.append(f"- {occ}")
            lines.append("")

        # Activities grouped by area (deduplicated)
        atividades = fam.get("atividades", [])
        if atividades:
            lines.append("## Atividades")
            # Group by area, dedup within each area
            by_area: dict[str, list[str]] = {}
            for at in atividades:
                area = at["area"]
                if area not in by_area:
                    by_area[area] = []
                if at["atividade"] not in by_area[area]:
                    by_area[area].append(at["atividade"])

            for area, acts in by_area.items():
                lines.append(f"\n### {area}")
                for act in acts:
                    lines.append(f"- {act}")
            lines.append("")
        else:
            lines.append("(Atividades detalhadas não disponíveis no perfil ocupacional CBO.)")
            lines.append("")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        generated += 1

        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(familias)}] generated...")

    print(f"\nDone: {generated} generated, {cached} cached out of {len(subset)}")




# ---------------------------------------------------------------------------
# Step 4: Build master JSON
# ---------------------------------------------------------------------------
def build_master_json(familias: list[dict]):
    """Build the master occupations JSON for the Brazil pipeline."""
    out_path = os.path.join(DATA_DIR, "cbo_occupations.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(familias, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(familias)} families to {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Scrape CBO occupation data")
    parser.add_argument("--csv-only", action="store_true", help="Only download CSVs")
    parser.add_argument("--desc-only", action="store_true", help="Only scrape descriptions")
    parser.add_argument("--force", action="store_true", help="Re-download/scrape even if cached")
    parser.add_argument("--start", type=int, default=0, help="Start index for page generation")
    parser.add_argument("--end", type=int, default=None, help="End index for page generation")
    args = parser.parse_args()

    if not args.desc_only:
        print("Step 1: Downloading CBO CSVs from gov.br...")
        download_csvs(force=args.force)

    if args.csv_only:
        # Still build the JSON from CSVs
        print("\nStep 2: Building master occupation list...")
        familias = load_familias()
        build_master_json(familias)
        return

    print("\nStep 2: Loading CBO family data...")
    familias = load_familias()
    build_master_json(familias)

    end = args.end if args.end is not None else len(familias)
    print(f"\nStep 3: Generating description pages ({args.start} to {end} of {len(familias)} families)...")
    generate_pages(familias, args.start, end, args.force)

    # Count pages
    if os.path.exists(PAGES_DIR):
        pages = len([f for f in os.listdir(PAGES_DIR) if f.endswith(".md")])
        print(f"\nTotal: {pages}/{len(familias)} description pages in {PAGES_DIR}/")


if __name__ == "__main__":
    main()
