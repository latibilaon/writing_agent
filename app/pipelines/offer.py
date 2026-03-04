from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass
from pathlib import Path

from ..converter import convert_tree, load_markdown_bundle
from ..docx_utils import markdown_to_docx
from ..openrouter_client import OpenRouterClient

SECTIONS = [
    "Demonstrated Academic and Language Readiness",
    "Exceptional Profile and Program Alignment",
    "Unwavering Commitment to the University",
]


@dataclass
class OfferRequest:
    school: str
    request: str
    professor_url: str = ""
    program_url: str = ""
    target_program: str = ""
    student_name_override: str = ""
    extra_instructions: str = ""
    model: str = "anthropic/claude-sonnet-4.6"
    word_min: int = 750
    word_max: int = 900
    materials_dir: Path | None = None
    converted_dir: Path | None = None
    output_dir: Path | None = None
    skip_convert: bool = False
    retries: int = 1


def _slug(value: str) -> str:
    s = re.sub(r"\s+", "_", value.strip())
    return re.sub(r"[^A-Za-z0-9_\-]", "", s) or "Applicant"


def _count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _strip_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip()


def _extract_profile(client: OpenRouterClient, req: OfferRequest, bundle: str, logger) -> dict:
    prompt = f"""Extract student profile facts from the provided materials and output STRICT JSON only.

Rules:
- Use only evidence from materials.
- If a field is unknown, return an empty string.
- Do not fabricate.
- Output JSON object only.

JSON schema:
{{
  "student_name": "",
  "target_program": "",
  "offer_type": "",
  "current_conditions": "",
  "unmet_condition": "",
  "academic_evidence": "",
  "exceptional_profile": "",
  "program_alignment": "",
  "commitment_to_school": "",
  "special_circumstances": "",
  "english_competency_notes": ""
}}

Context:
- Target school: {req.school}
- Requested revision: {req.request}
- Program hint: {req.target_program}

Materials:
{bundle if bundle else '[No materials]'}
"""
    raw, usage = client.chat(req.model, prompt, x_title="Uoffer Portable Offer Profile Extract")
    logger.info(f"[INFO] extract usage: prompt={usage.get('prompt_tokens')} completion={usage.get('completion_tokens')}")
    raw = _strip_fences(raw)
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not m:
            logger.warn("[WARN] Could not parse extraction JSON; use empty profile.")
            return {}
        try:
            return json.loads(m.group(0))
        except Exception:
            logger.warn("[WARN] Could not parse extraction JSON; use empty profile.")
            return {}


def _build_letter_prompt(case: dict, req: OfferRequest, bundle: str) -> str:
    sections_text = "\n".join(f"{i+1}) {s}" for i, s in enumerate(SECTIONS))
    today = datetime.date.today().strftime("%d %B %Y")
    return f"""You are an elite admissions appeal writer.

Task:
Write one complete English appeal letter in Markdown.
Do NOT output outline, notes, or explanations.
Output only the final letter.

Mandatory constraints:
- Word count: {req.word_min} to {req.word_max}
- Structure must use these section headings exactly:
{sections_text}
- Add one concise final paragraph that explicitly requests the revision below.
- Academic writing style with clear logic and concrete evidence.
- Low AI trace: avoid repetitive generic phrasing and empty rhetorical padding.
- No fabricated facts, scores, courses, awards, or incidents.

Specific quality requirements:
1) In section 1, discuss readiness with verifiable evidence from materials.
   If exact course names/scores are missing, stay factual and non-specific.
2) In section 2, prioritize candidate qualities and fit; avoid score listing.
3) In section 3, show concrete commitment and future contribution.

Date: {today}

Core case data:
- Student name: {case.get('student_name', '')}
- Target university: {case.get('target_university', '')}
- Target program: {case.get('target_program', '')}
- Offer type: {case.get('offer_type', '')}
- Current conditions: {case.get('current_conditions', '')}
- Unmet condition: {case.get('unmet_condition', '')}
- Requested revision: {case.get('requested_revision', '')}
- Academic evidence: {case.get('academic_evidence', '')}
- Exceptional profile: {case.get('exceptional_profile', '')}
- Program alignment: {case.get('program_alignment', '')}
- Commitment to school: {case.get('commitment_to_school', '')}
- Special circumstances: {case.get('special_circumstances', '')}
- English competency notes: {case.get('english_competency_notes', '')}
- Program URL: {case.get('program_url', '')}
- Professor URL: {case.get('professor_url', '')}
- Extra instructions: {req.extra_instructions}

Source materials:
{bundle if bundle else '[No materials]'}
"""


def _validate_letter(letter: str, req: OfferRequest) -> list[str]:
    issues = []
    wc = _count_words(letter)
    if wc < req.word_min or wc > req.word_max:
        issues.append(f"Word count {wc} outside {req.word_min}-{req.word_max}.")
    low = letter.lower()
    for s in SECTIONS:
        if s.lower() not in low:
            issues.append(f"Missing section heading: {s}")
    key = req.request.strip().lower()[:36]
    if key and key not in low:
        issues.append("Requested revision not clearly reflected.")
    return issues


def _revision_prompt(draft: str, issues: list[str], req: OfferRequest) -> str:
    bullet = "\n".join(f"- {x}" for x in issues)
    return f"""Revise the following appeal letter and return only the final Markdown letter.

Keep constraints:
- Word count {req.word_min}-{req.word_max}
- Keep exact section headings
- Keep facts only; do not invent

Fix issues:
{bullet}

Draft:
{draft}
"""


def run_offer_pipeline(req: OfferRequest, client: OpenRouterClient, logger):
    logger.head("=" * 60)
    logger.head("STEP 1  Materials -> Markdown")
    logger.head("=" * 60)
    req.converted_dir.mkdir(parents=True, exist_ok=True)
    req.output_dir.mkdir(parents=True, exist_ok=True)
    if not req.skip_convert:
        convert_tree(req.materials_dir, req.converted_dir, logger)
    else:
        logger.warn("[SKIP] conversion skipped by user")

    bundle = load_markdown_bundle(req.converted_dir)

    logger.head("=" * 60)
    logger.head("STEP 2  Auto-Read Student Profile")
    logger.head("=" * 60)
    profile = _extract_profile(client, req, bundle, logger)

    case = {
        "student_name": req.student_name_override or profile.get("student_name", ""),
        "target_university": req.school,
        "target_program": req.target_program or profile.get("target_program", ""),
        "offer_type": profile.get("offer_type", "Conditional Offer"),
        "current_conditions": profile.get("current_conditions", ""),
        "unmet_condition": profile.get("unmet_condition", ""),
        "requested_revision": req.request,
        "academic_evidence": profile.get("academic_evidence", ""),
        "exceptional_profile": profile.get("exceptional_profile", ""),
        "program_alignment": profile.get("program_alignment", ""),
        "commitment_to_school": profile.get("commitment_to_school", ""),
        "special_circumstances": profile.get("special_circumstances", ""),
        "english_competency_notes": profile.get("english_competency_notes", ""),
        "program_url": req.program_url,
        "professor_url": req.professor_url,
    }

    logger.head("=" * 60)
    logger.head("STEP 3  One-shot Letter Generation")
    logger.head("=" * 60)
    prompt = _build_letter_prompt(case, req, bundle)
    letter, usage = client.chat(req.model, prompt, x_title="Uoffer Portable Offer Letter")
    logger.info(f"[INFO] generate usage: prompt={usage.get('prompt_tokens')} completion={usage.get('completion_tokens')}")

    issues = _validate_letter(letter, req)
    retry = 0
    while issues and retry < max(0, req.retries):
        retry += 1
        logger.warn(f"[WARN] validation failed, revising ({retry}/{req.retries})")
        rev_prompt = _revision_prompt(letter, issues, req)
        letter, _ = client.chat(req.model, rev_prompt, x_title="Uoffer Portable Offer Revision")
        issues = _validate_letter(letter, req)

    if issues:
        for i in issues:
            logger.warn(f"[WARN] {i}")

    logger.head("=" * 60)
    logger.head("STEP 4  Save Output")
    logger.head("=" * 60)

    day = datetime.date.today().strftime("%Y%m%d")
    student = _slug(case.get("student_name") or "Applicant")
    school = _slug(req.school)
    md_path = req.output_dir / f"Appeal_{student}_{school}_{day}.md"
    md_path.write_text(letter.strip() + "\n", encoding="utf-8")
    logger.ok(f"[OK] Saved: {md_path}")

    docx_path = req.output_dir / f"Appeal_{student}_{school}_{day}.docx"
    try:
        markdown_to_docx(letter, docx_path)
        logger.ok(f"[OK] Saved: {docx_path}")
    except Exception as exc:
        docx_path = None
        logger.warn(f"[WARN] docx export skipped: {exc}")

    logger.info(f"[INFO] word count: {_count_words(letter)}")
    return {"markdown": md_path, "docx": docx_path, "case": case}
