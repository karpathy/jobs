#!/usr/bin/env python3
"""
Validate CBO (Classificação Brasileira de Ocupações) scraped data.
Checks counts, hierarchy integrity, coverage, page quality, and specific occupations.
"""

import csv
import json
import os
import random
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PAGES_DIR = os.path.join(os.path.dirname(__file__), "pages")

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

results = []

def report(status, message):
    results.append((status, message))
    icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[status]
    print(f"  {icon} {message}")


def read_csv(filename):
    """Read a semicolon-delimited Latin-1 CSV, strip whitespace from fields."""
    path = os.path.join(DATA_DIR, filename)
    rows = []
    with open(path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            rows.append(cleaned)
    return rows


def load_json():
    path = os.path.join(DATA_DIR, "cbo_occupations.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────
# 1. COUNTS
# ─────────────────────────────────────────────────────────────────────
def check_counts():
    print("\n" + "=" * 70)
    print("1. COUNTS — entries at each CBO hierarchy level")
    print("=" * 70)

    gg = read_csv("cbo2002-grande-grupo.csv")
    sp = read_csv("cbo2002-subgrupo-principal.csv")
    sg = read_csv("cbo2002-subgrupo.csv")
    fm = read_csv("cbo2002-familia.csv")
    oc = read_csv("cbo2002-ocupacao.csv")
    js = load_json()

    expected = {
        "Grande Grupo":       (10, len(gg)),
        "Subgrupo Principal": (48, len(sp)),
        "Subgrupo":           (192, len(sg)),
        "Família":            (596, len(fm)),
        "Ocupação":           (2500, len(oc)),
    }

    print(f"\n  {'Level':<25} {'Expected ~':<12} {'Actual':<10} Status")
    print(f"  {'-'*25} {'-'*12} {'-'*10} {'-'*6}")
    for name, (exp, act) in expected.items():
        # Allow ±15% tolerance for approximate expectations
        lo, hi = int(exp * 0.80), int(exp * 1.20)
        ok = lo <= act <= hi
        status = PASS if ok else WARN
        report(status, f"{name}: expected ~{exp}, got {act}")

    # JSON vs CSV familia consistency
    json_codes = {e["codigo"] for e in js}
    csv_codes = {r["CODIGO"] for r in fm}
    if json_codes == csv_codes:
        report(PASS, f"JSON familias ({len(json_codes)}) match CSV familias ({len(csv_codes)}) exactly")
    else:
        only_json = json_codes - csv_codes
        only_csv = csv_codes - json_codes
        report(FAIL, f"JSON vs CSV familia mismatch: {len(only_json)} only in JSON, {len(only_csv)} only in CSV")
        if only_json:
            print(f"    Only in JSON (first 10): {sorted(only_json)[:10]}")
        if only_csv:
            print(f"    Only in CSV  (first 10): {sorted(only_csv)[:10]}")

    # Pages vs JSON
    page_files = [f for f in os.listdir(PAGES_DIR) if f.endswith(".md")]
    page_codes = {f.split("-")[0] for f in page_files}
    if len(page_files) == len(js):
        report(PASS, f"Page count ({len(page_files)}) matches JSON entries ({len(js)})")
    else:
        report(WARN, f"Page count ({len(page_files)}) differs from JSON entries ({len(js)})")
        missing_pages = json_codes - page_codes
        extra_pages = page_codes - json_codes
        if missing_pages:
            print(f"    Missing pages (first 10): {sorted(missing_pages)[:10]}")
        if extra_pages:
            print(f"    Extra pages   (first 10): {sorted(extra_pages)[:10]}")


# ─────────────────────────────────────────────────────────────────────
# 2. HIERARCHY INTEGRITY
# ─────────────────────────────────────────────────────────────────────
def check_hierarchy():
    print("\n" + "=" * 70)
    print("2. HIERARCHY INTEGRITY")
    print("=" * 70)

    gg_codes = {r["CODIGO"] for r in read_csv("cbo2002-grande-grupo.csv")}
    sp_codes = {r["CODIGO"] for r in read_csv("cbo2002-subgrupo-principal.csv")}
    sg_codes = {r["CODIGO"] for r in read_csv("cbo2002-subgrupo.csv")}
    fm_rows = read_csv("cbo2002-familia.csv")
    oc_rows = read_csv("cbo2002-ocupacao.csv")
    js = load_json()

    # Check familia codes map to valid parents
    fm_no_gg, fm_no_sp, fm_no_sg = [], [], []
    for r in fm_rows:
        code = r["CODIGO"]  # 4 digits
        gg_prefix = code[0]
        sp_prefix = code[:2]
        sg_prefix = code[:3]
        if gg_prefix not in gg_codes:
            fm_no_gg.append(code)
        if sp_prefix not in sp_codes:
            fm_no_sp.append(code)
        if sg_prefix not in sg_codes:
            fm_no_sg.append(code)

    if not fm_no_gg:
        report(PASS, f"All {len(fm_rows)} familias map to a valid grande grupo")
    else:
        report(FAIL, f"{len(fm_no_gg)} familias have no valid grande grupo: {fm_no_gg[:10]}")

    if not fm_no_sp:
        report(PASS, f"All {len(fm_rows)} familias map to a valid subgrupo principal")
    else:
        report(FAIL, f"{len(fm_no_sp)} familias have no valid subgrupo principal: {fm_no_sp[:10]}")

    if not fm_no_sg:
        report(PASS, f"All {len(fm_rows)} familias map to a valid subgrupo")
    else:
        report(FAIL, f"{len(fm_no_sg)} familias have no valid subgrupo: {fm_no_sg[:10]}")

    # Check ocupacoes map to valid familias
    fm_codes = {r["CODIGO"] for r in fm_rows}
    oc_no_fm = []
    for r in oc_rows:
        code = r["CODIGO"]  # 6 digits
        fm_prefix = code[:4]
        if fm_prefix not in fm_codes:
            oc_no_fm.append(code)
    if not oc_no_fm:
        report(PASS, f"All {len(oc_rows)} ocupacoes map to a valid familia")
    else:
        report(FAIL, f"{len(oc_no_fm)} ocupacoes have no valid familia: {oc_no_fm[:10]}")

    # Check JSON hierarchy fields are consistent with the code
    json_hierarchy_errors = []
    for entry in js:
        code = entry["codigo"]
        if entry.get("grande_grupo_codigo") != code[0]:
            json_hierarchy_errors.append((code, "grande_grupo_codigo", entry.get("grande_grupo_codigo"), code[0]))
        if entry.get("subgrupo_principal_codigo") != code[:2]:
            json_hierarchy_errors.append((code, "subgrupo_principal_codigo", entry.get("subgrupo_principal_codigo"), code[:2]))
        if entry.get("subgrupo_codigo") != code[:3]:
            json_hierarchy_errors.append((code, "subgrupo_codigo", entry.get("subgrupo_codigo"), code[:3]))

    if not json_hierarchy_errors:
        report(PASS, f"All JSON entries have consistent hierarchy codes")
    else:
        report(FAIL, f"{len(json_hierarchy_errors)} JSON entries have inconsistent hierarchy codes")
        for code, field, got, expected in json_hierarchy_errors[:5]:
            print(f"    {code}: {field} = '{got}', expected '{expected}'")


# ─────────────────────────────────────────────────────────────────────
# 3. COVERAGE — perfil ocupacional activities
# ─────────────────────────────────────────────────────────────────────
def check_coverage():
    print("\n" + "=" * 70)
    print("3. COVERAGE — perfil ocupacional / activities")
    print("=" * 70)

    js = load_json()
    perfil = read_csv("cbo2002-perfilocupacional.csv")

    # Families in perfil
    perfil_familias = {r["COD_FAMILIA"] for r in perfil}
    json_codes = {e["codigo"] for e in js}

    with_activities = sum(1 for e in js if e.get("atividades"))
    without_activities = sum(1 for e in js if not e.get("atividades"))
    with_areas = sum(1 for e in js if e.get("areas_de_atividade"))

    report(PASS if with_activities > 0 else FAIL,
           f"JSON entries with activities: {with_activities}/{len(js)} ({100*with_activities/len(js):.1f}%)")
    report(WARN if without_activities > 0 else PASS,
           f"JSON entries with ZERO activities: {without_activities}/{len(js)}")
    report(PASS if with_areas > 0 else FAIL,
           f"JSON entries with areas_de_atividade: {with_areas}/{len(js)}")

    # Which familias have perfil data?
    covered = json_codes & perfil_familias
    not_covered = json_codes - perfil_familias
    report(PASS if len(covered) > len(json_codes) * 0.8 else WARN,
           f"Familias with perfil data: {len(covered)}/{len(json_codes)}")
    if not_covered:
        # Group by grande grupo
        from collections import Counter
        gg_missing = Counter(c[0] for c in not_covered)
        print(f"    Familias without perfil data by grande grupo: {dict(sorted(gg_missing.items()))}")

    # Activity count distribution
    act_counts = [len(e.get("atividades", [])) for e in js]
    print(f"\n  Activity count distribution:")
    print(f"    Min: {min(act_counts)}, Max: {max(act_counts)}, "
          f"Median: {sorted(act_counts)[len(act_counts)//2]}, "
          f"Mean: {sum(act_counts)/len(act_counts):.1f}")


# ─────────────────────────────────────────────────────────────────────
# 4. PAGE QUALITY — sample pages across grande grupos
# ─────────────────────────────────────────────────────────────────────
def check_page_quality():
    print("\n" + "=" * 70)
    print("4. PAGE QUALITY — sampled pages")
    print("=" * 70)

    js = load_json()
    # Pick 1-2 entries per grande grupo, preferring ones with activities
    from collections import defaultdict
    by_gg = defaultdict(list)
    for e in js:
        by_gg[e["grande_grupo_codigo"]].append(e)

    samples = []
    random.seed(42)
    for gg in sorted(by_gg.keys()):
        with_act = [e for e in by_gg[gg] if e.get("atividades")]
        pool = with_act if with_act else by_gg[gg]
        samples.append(random.choice(pool))

    print(f"\n  Sampling {len(samples)} pages (one per grande grupo):\n")
    for entry in samples:
        code = entry["codigo"]
        slug = entry["slug"]
        page_path = os.path.join(PAGES_DIR, f"{slug}.md")
        exists = os.path.isfile(page_path)
        if not exists:
            report(FAIL, f"  Page missing for {code} - {entry['titulo']}")
            continue

        with open(page_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        has_title = lines[0].startswith("# ") if lines else False
        has_code = f"**Código CBO:** {code}" in content
        has_activities = "## Atividades" in content
        has_ocupacoes = "## Ocupações" in content
        word_count = len(content.split())

        status = PASS if (has_title and has_code and word_count > 30) else WARN
        act_flag = "activities" if has_activities else "NO activities"
        ocu_flag = "ocupacoes" if has_ocupacoes else "NO ocupacoes"
        report(status, f"Page {code} ({entry['titulo'][:40]}): {word_count} words, {act_flag}, {ocu_flag}")


# ─────────────────────────────────────────────────────────────────────
# 5. SPOT CHECK — known occupations
# ─────────────────────────────────────────────────────────────────────
def check_spot():
    print("\n" + "=" * 70)
    print("5. SPOT CHECK — known occupation families")
    print("=" * 70)

    js = load_json()
    by_code = {e["codigo"]: e for e in js}
    oc_rows = read_csv("cbo2002-ocupacao.csv")
    oc_by_familia = {}
    for r in oc_rows:
        fm = r["CODIGO"][:4]
        oc_by_familia.setdefault(fm, []).append(r)

    checks = [
        ("2124", "Analistas de TI / tecnologia da informação"),
        ("7152", "Pedreiros / alvenaria"),
        ("5211", "Operadores do comércio"),
        ("2251", "Médicos clínicos"),
        ("7823", "Motoristas de veículos pequeno/médio porte"),
        ("4223", "Operadores de telemarketing"),
        ("2521", "Administradores"),
    ]

    print()
    for code, description in checks:
        entry = by_code.get(code)
        if not entry:
            report(FAIL, f"{code} ({description}): NOT FOUND in JSON")
            continue

        n_activities = len(entry.get("atividades", []))
        n_areas = len(entry.get("areas_de_atividade", []))
        n_ocups = len(oc_by_familia.get(code, []))
        titulo = entry["titulo"]

        # Check page exists
        page_path = os.path.join(PAGES_DIR, f"{entry['slug']}.md")
        page_exists = os.path.isfile(page_path)

        status = PASS if (n_activities > 0 and page_exists) else WARN
        report(status, f"{code} \"{titulo}\"")
        print(f"         Areas: {n_areas}, Activities: {n_activities}, "
              f"Sub-occupations in CSV: {n_ocups}, Page: {'exists' if page_exists else 'MISSING'}")


# ─────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────
def print_summary():
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passes = sum(1 for s, _ in results if s == PASS)
    warns = sum(1 for s, _ in results if s == WARN)
    fails = sum(1 for s, _ in results if s == FAIL)
    total = len(results)
    print(f"\n  Total checks: {total}")
    print(f"  [PASS]: {passes}")
    print(f"  [WARN]: {warns}")
    print(f"  [FAIL]: {fails}")

    if fails:
        print("\n  FAILURES:")
        for s, m in results:
            if s == FAIL:
                print(f"    - {m}")
    if warns:
        print("\n  WARNINGS:")
        for s, m in results:
            if s == WARN:
                print(f"    - {m}")

    print()
    if fails == 0:
        print("  OVERALL: Data looks good. No critical failures.")
    else:
        print("  OVERALL: Critical issues found. Please review failures above.")


if __name__ == "__main__":
    print("CBO Data Validation Report")
    print("=" * 70)
    check_counts()
    check_hierarchy()
    check_coverage()
    check_page_quality()
    check_spot()
    print_summary()
