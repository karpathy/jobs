"""
Score each Brazilian occupation's AI metrics using an LLM via OpenRouter.

Reads Markdown descriptions from brazil/pages/, sends each to an LLM with
Portuguese scoring rubrics, and collects structured scores.

Metrics:
  - exposicao: How much AI will reshape this occupation (0-10)
  - vantagem: How much workers benefit from adopting AI (0-10)
  - crescimento: How AI will affect demand for the occupation (0-10)

Results are cached incrementally per-metric so the script can be resumed.

Usage:
    uv run python brazil/score_br.py                          # default: exposicao
    uv run python brazil/score_br.py --metric vantagem
    uv run python brazil/score_br.py --metric crescimento
    uv run python brazil/score_br.py --start 0 --end 10       # test on first 10
    uv run python brazil/score_br.py --force                   # re-score all
"""

import argparse
import json
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "google/gemini-3-flash-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

PAGES_DIR = "brazil/pages"
SCORES_DIR = "brazil/scores"

# ── Prompts (Portuguese, Brazilian context) ──────────────────────────────

EXPOSICAO_PROMPT = """\
Você é um analista especializado avaliando a exposição de ocupações brasileiras \
à inteligência artificial. Você receberá uma descrição detalhada de uma ocupação \
da Classificação Brasileira de Ocupações (CBO).

Avalie a **Exposição à IA** desta ocupação em uma escala de 0 a 10.

Exposição à IA mede: quanto a IA vai transformar esta ocupação? Considere \
efeitos diretos (IA automatizando tarefas feitas por humanos) e indiretos \
(IA tornando cada trabalhador tão produtivo que menos são necessários).

Um sinal importante é se o trabalho é fundamentalmente digital. Se o trabalho \
pode ser feito inteiramente de um computador — escrever, programar, analisar, \
comunicar — então a exposição é inerentemente alta (7+), porque as capacidades \
da IA em domínios digitais estão avançando rapidamente. Trabalhos que exigem \
presença física, habilidade manual ou interação humana no mundo físico têm \
uma barreira natural à exposição.

Considere também o contexto brasileiro:
- Nível de digitalização do setor no Brasil
- Infraestrutura tecnológica (internet, acesso a ferramentas de IA)
- Velocidade de adoção tecnológica no Brasil vs países desenvolvidos

Use estas âncoras para calibrar sua pontuação:

- **0–1: Exposição mínima.** Trabalho quase inteiramente físico, manual, em \
ambientes imprevisíveis. IA não impacta o trabalho diário. \
Exemplos: pedreiro, pescador artesanal, trabalhador rural.

- **2–3: Exposição baixa.** Trabalho majoritariamente físico ou presencial. \
IA pode ajudar com tarefas periféricas (agendamento, papelada) mas não toca \
o trabalho principal. \
Exemplos: eletricista, bombeiro, cuidador de idosos, motorista de ônibus.

- **4–5: Exposição moderada.** Mistura de trabalho físico/presencial e \
trabalho intelectual. IA pode auxiliar significativamente nas partes de \
processamento de informação. \
Exemplos: enfermeiro, policial, veterinário, técnico de enfermagem.

- **6–7: Exposição alta.** Trabalho predominantemente intelectual com alguma \
necessidade de julgamento humano ou presença física. Ferramentas de IA já \
são úteis e trabalhadores que usam IA são mais produtivos. \
Exemplos: professor, gerente, contador, jornalista, administrador.

- **8–9: Exposição muito alta.** Trabalho quase inteiramente feito no \
computador. Todas as tarefas centrais estão em domínios onde a IA avança \
rapidamente. A ocupação enfrenta reestruturação significativa. \
Exemplos: desenvolvedor de software, designer gráfico, tradutor, analista \
de dados, analista de TI.

- **10: Exposição máxima.** Processamento rotineiro de informação, totalmente \
digital, sem componente físico. IA já pode fazer a maior parte hoje. \
Exemplos: digitador, operador de telemarketing.

Responda com APENAS um objeto JSON neste formato exato, sem outro texto:
{
  "exposicao": <0-10>,
  "rationale": "<2-3 frases em português explicando os fatores principais>"
}\
"""

VANTAGEM_PROMPT = """\
Você é um analista especializado avaliando quanto trabalhadores brasileiros \
podem se beneficiar ao adotar ferramentas de IA. Você receberá uma descrição \
detalhada de uma ocupação da CBO.

Avalie a **Vantagem com IA** desta ocupação em uma escala de 0 a 10.

Vantagem com IA mede: quanto um trabalhador nesta ocupação pode ampliar sua \
produtividade e competitividade ao adotar ferramentas de IA? Considere:
- A IA pode automatizar partes repetitivas, liberando tempo para tarefas de maior valor?
- Usar IA cria uma diferença significativa entre quem adota e quem não adota?
- Quanto mais rápido/melhor o produto do trabalho pode ficar com assistência de IA?

Considere o contexto brasileiro:
- Acesso a ferramentas de IA no Brasil (custo, disponibilidade em português)
- Barreira linguística — muitas ferramentas são em inglês
- Nível de letramento digital dos trabalhadores no setor

Use estas âncoras:

- **0–1: Mínima.** Trabalho físico/manual, ferramentas de IA pouco relevantes. \
Exemplos: pedreiro, trabalhador rural, pescador.

- **2–3: Baixa.** Trabalho majoritariamente manual; IA ajuda com papelada mas não com trabalho central. \
Exemplos: eletricista, bombeiro, motorista de caminhão.

- **4–5: Moderada.** Mistura de trabalho físico e intelectual; IA auxilia nas partes administrativas. \
Exemplos: enfermeiro, veterinário, técnico de laboratório.

- **6–7: Alta.** Trabalho intelectual; ferramentas de IA já aumentam produtividade significativamente. \
Exemplos: professor, contador, advogado, analista financeiro.

- **8–9: Muito alta.** Trabalho quase inteiramente digital; copilots de IA transformam todas as tarefas. \
Exemplos: desenvolvedor de software, designer gráfico, analista de dados.

- **10: Máxima.** IA pode lidar com quase todas as tarefas; adotantes são dramaticamente mais produtivos. \
Exemplos: digitador, redator publicitário.

Responda com APENAS um objeto JSON neste formato exato, sem outro texto:
{
  "vantagem": <0-10>,
  "rationale": "<2-3 frases em português explicando os fatores principais>"
}\
"""

CRESCIMENTO_PROMPT = """\
Você é um analista especializado avaliando como a IA vai afetar a demanda \
por diferentes ocupações no Brasil. Você receberá uma descrição detalhada \
de uma ocupação da CBO.

Avalie o **Crescimento com IA** desta ocupação em uma escala de 0 a 10.

Crescimento com IA mede: quanto a IA vai expandir a demanda, criar novos \
sub-papéis, ou crescer o mercado para esta ocupação? Considere:
- A IA vai tornar este serviço mais barato/rápido, liberando demanda latente?
- A IA cria novos domínios de problemas que precisam desta ocupação?
- Ganhos de produtividade vão levar a mais contratações (demanda elástica) ou menos (inelástica)?
- Fatores regulatórios, de confiança ou sociais que sustentam ou crescem a demanda?

Considere o contexto brasileiro:
- Regulação trabalhista (CLT) que pode retardar substituição
- Custo de mão de obra vs custo de automação no Brasil
- Demanda reprimida por serviços que IA pode tornar acessíveis
- Crescimento de setores específicos da economia brasileira

Use estas âncoras:

- **0–1: Encolhendo.** IA substitui demanda diretamente; menos trabalhadores necessários. \
Exemplos: digitador, operador de telemarketing.

- **2–3: Estável.** IA não muda significativamente a demanda. \
Exemplos: pedreiro, motorista de ônibus, ajudante de obras.

- **4–5: Estável+.** Nova demanda adjacente à IA compensa parcialmente automação. \
Exemplos: contador, técnico administrativo.

- **6–7: Crescendo.** IA cria demanda significativa nova ou torna serviço mais acessível. \
Exemplos: enfermeiro, professor, eletricista, técnico em TI.

- **8–9: Forte crescimento.** IA abre novos mercados ou sub-especialidades importantes. \
Exemplos: analista de segurança cibernética, engenheiro de dados.

- **10: Explosivo.** Demanda inteiramente nova impulsionada pela IA. \
Exemplos: engenheiro de IA/ML, especialista em automação inteligente.

Responda com APENAS um objeto JSON neste formato exato, sem outro texto:
{
  "crescimento": <0-10>,
  "rationale": "<2-3 frases em português explicando os fatores principais>"
}\
"""

METRIC_CONFIG = {
    "exposicao": {
        "prompt": EXPOSICAO_PROMPT,
        "output_file": os.path.join(SCORES_DIR, "scores_exposicao.json"),
        "score_key": "exposicao",
    },
    "vantagem": {
        "prompt": VANTAGEM_PROMPT,
        "output_file": os.path.join(SCORES_DIR, "scores_vantagem.json"),
        "score_key": "vantagem",
    },
    "crescimento": {
        "prompt": CRESCIMENTO_PROMPT,
        "output_file": os.path.join(SCORES_DIR, "scores_crescimento.json"),
        "score_key": "crescimento",
    },
}


def score_occupation(client, text, model, system_prompt):
    """Send one occupation to the LLM and parse the structured response."""
    response = client.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--metric", default="exposicao",
                        choices=["exposicao", "vantagem", "crescimento"],
                        help="Which metric to score (default: exposicao)")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.3)
    parser.add_argument("--force", action="store_true",
                        help="Re-score even if already cached")
    args = parser.parse_args()

    os.makedirs(SCORES_DIR, exist_ok=True)

    cfg = METRIC_CONFIG[args.metric]
    output_file = cfg["output_file"]
    score_key = cfg["score_key"]
    system_prompt = cfg["prompt"]

    with open("brazil/data/cbo_occupations.json", encoding="utf-8") as f:
        occupations = json.load(f)

    subset = occupations[args.start:args.end]

    # Load existing scores
    scores = {}
    if os.path.exists(output_file) and not args.force:
        with open(output_file, encoding="utf-8") as f:
            for entry in json.load(f):
                scores[entry["slug"]] = entry

    print(f"Scoring {len(subset)} occupations for '{args.metric}' with {args.model}")
    print(f"Output: {output_file}")
    print(f"Already cached: {len(scores)}")

    errors = []
    client = httpx.Client()

    for i, occ in enumerate(subset):
        slug = occ["slug"]

        if slug in scores:
            continue

        md_path = os.path.join(PAGES_DIR, f"{slug}.md")
        if not os.path.exists(md_path):
            print(f"  [{i+1}] SKIP {slug} (no markdown)")
            continue

        with open(md_path, encoding="utf-8") as f:
            text = f.read()

        print(f"  [{i+1}/{len(subset)}] {occ['titulo']}...", end=" ", flush=True)

        try:
            result = score_occupation(client, text, args.model, system_prompt)
            scores[slug] = {
                "slug": slug,
                "codigo": occ["codigo"],
                "titulo": occ["titulo"],
                **result,
            }
            print(f"{score_key}={result[score_key]}")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(slug)

        # Save after each one (incremental checkpoint)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(list(scores.values()), f, ensure_ascii=False, indent=2)

        if i < len(subset) - 1:
            time.sleep(args.delay)

    client.close()

    print(f"\nDone. Scored {len(scores)} occupations, {len(errors)} errors.")
    if errors:
        print(f"Errors: {errors}")

    # Summary stats
    vals = [s for s in scores.values() if score_key in s]
    if vals:
        avg = sum(s[score_key] for s in vals) / len(vals)
        by_score = {}
        for s in vals:
            bucket = s[score_key]
            by_score[bucket] = by_score.get(bucket, 0) + 1
        print(f"\nAverage {score_key} across {len(vals)} occupations: {avg:.1f}")
        print("Distribution:")
        for k in sorted(by_score):
            print(f"  {k}: {'█' * by_score[k]} ({by_score[k]})")


if __name__ == "__main__":
    main()
