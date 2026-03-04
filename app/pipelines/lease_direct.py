from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from pathlib import Path

from ..converter import convert_tree, load_markdown_bundle
from ..docx_utils import markdown_to_docx
from ..openrouter_client import OpenRouterClient


@dataclass
class LeaseDirectRequest:
    tenant_name: str
    property_address: str
    termination_deadline: str
    refund_amount: str
    issues: str
    health_context: str
    jurisdiction: str
    demands: str
    model: str
    materials_dir: Path
    converted_dir: Path
    output_dir: Path
    skip_convert: bool = False
    retries: int = 1


def _slug(value: str) -> str:
    s = re.sub(r"\s+", "_", value.strip())
    return re.sub(r"[^A-Za-z0-9_\-]", "", s) or "Tenant"


def _count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _analysis_prompt(req: LeaseDirectRequest, bundle: str) -> str:
    return f"""You are a tenancy contract analyst.
Extract landlord-side breaches and supporting contract evidence from the provided materials.
Output in English markdown bullet points.

Tenant-reported issues:
{req.issues}

Materials:
{bundle if bundle else '[No materials]'}
"""


def _letter_prompt(req: LeaseDirectRequest, analysis: str) -> str:
    today = datetime.date.today().strftime("%d %B %Y")
    return f"""Write a formal lease termination and refund demand letter in English Markdown.
Do not output notes or analysis, only final letter.

Must include sections:
1) Background and request
2) Contractual/Habitability breaches
3) Legal grounds ({req.jurisdiction})
4) Settlement request and response deadline

Constraints:
- Tone: professional, firm, legally coherent
- Include explicit request: terminate by {req.termination_deadline}, refund {req.refund_amount}
- Avoid fabricated facts

Case facts:
- Date: {today}
- Tenant: {req.tenant_name}
- Address: {req.property_address}
- Deadline: {req.termination_deadline}
- Refund amount: {req.refund_amount}
- Jurisdiction: {req.jurisdiction}
- Health context: {req.health_context}
- Tenant demands: {req.demands}

Extracted contract analysis:
{analysis}
"""


def run_lease_direct_pipeline(req: LeaseDirectRequest, client: OpenRouterClient, logger):
    logger.head("=" * 60)
    logger.head("STEP 1  Contract Materials -> Markdown")
    logger.head("=" * 60)
    req.converted_dir.mkdir(parents=True, exist_ok=True)
    req.output_dir.mkdir(parents=True, exist_ok=True)
    if not req.skip_convert:
        convert_tree(req.materials_dir, req.converted_dir, logger)
    else:
        logger.warn("[SKIP] conversion skipped by user")

    bundle = load_markdown_bundle(req.converted_dir)

    logger.head("=" * 60)
    logger.head("STEP 2  Contract Analysis")
    logger.head("=" * 60)
    analysis, usage = client.chat(req.model, _analysis_prompt(req, bundle), x_title="Uoffer Portable Lease Analysis")
    logger.info(f"[INFO] analysis usage: prompt={usage.get('prompt_tokens')} completion={usage.get('completion_tokens')}")

    logger.head("=" * 60)
    logger.head("STEP 3  Direct Letter Generation")
    logger.head("=" * 60)
    letter, usage2 = client.chat(req.model, _letter_prompt(req, analysis), x_title="Uoffer Portable Lease Direct")
    logger.info(f"[INFO] generate usage: prompt={usage2.get('prompt_tokens')} completion={usage2.get('completion_tokens')}")

    logger.head("=" * 60)
    logger.head("STEP 4  Save Output")
    logger.head("=" * 60)
    day = datetime.date.today().strftime("%Y%m%d")
    slug = _slug(req.tenant_name)
    md_path = req.output_dir / f"Lease_Direct_{slug}_{day}.md"
    md_path.write_text(letter.strip() + "\n", encoding="utf-8")
    logger.ok(f"[OK] Saved: {md_path}")

    docx_path = req.output_dir / f"Lease_Direct_{slug}_{day}.docx"
    try:
        markdown_to_docx(letter, docx_path)
        logger.ok(f"[OK] Saved: {docx_path}")
    except Exception as exc:
        docx_path = None
        logger.warn(f"[WARN] docx export skipped: {exc}")

    logger.info(f"[INFO] word count: {_count_words(letter)}")
    return {"markdown": md_path, "docx": docx_path}
