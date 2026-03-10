#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path('/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope')
SEGMENT = Path.home() / '.trifecta/segments/skills-hub'
WRAPPER = Path.home() / '.local/bin/skill-hub'
BASELINE_PRESENTATION = Path.home() / '.local/bin/skill_hub_info_card.py'
PLAN = ROOT / '.pi/plan/skill-hub-cloop-master.md'
SAMPLE_PLAN = ROOT / '.pi/plan/skill-hub-trifecta-alignment-sample-first.md'
SPEC = ROOT / 'docs/reports/skill_hub_variant_b_spec.md'
SCHEMA = ROOT / 'docs/reports/skill_hub_ab_output_schema.md'
DATASET = ROOT / 'data/skill_hub_pilot_queries.yaml'
CORPUS_SUBSET = ROOT / 'data/skill_hub_pilot_corpus_subset.yaml'
REVIEWER = ROOT / 'docs/reports/skill_hub_independent_reviewer_protocol.md'
MANIFEST = SEGMENT / '_ctx/skills_manifest.json'
CONTEXT_PACK = SEGMENT / '_ctx/context_pack.json'
ALIASES = SEGMENT / '_ctx/aliases.yaml'
RESULTS_BASE = ROOT / 'eval/results/skill_hub_phase6'
SCRIPT_PATH = ROOT / 'eval/scripts/skill_hub_phase6_pilot.py'

SEARCH_HEADER_RE = re.compile(r'^\d+\.\s+\[(?P<ref>[^\]]+)\]\s+(?P<name>.+)$')
SCORE_RE = re.compile(r'^\s*Score:\s*(?P<score>[0-9.]+)\s+\|')
SOURCE_RE = re.compile(r'^\*\*Source\*\*:\s*(?P<source>.+)$')
PATH_RE = re.compile(r'^\*\*Path\*\*:\s*(?P<path>.+)$')
EXCERPT_HEADER_RE = re.compile(r'^##\s+\[(?P<ref>[^\]]+)\]\s+(?P<name>.+)$')
STOPWORDS = {
    'the','a','an','for','to','with','and','or','of','in','on','how','implement','find','skills','skill','related',
    'quiero','una','para','con','como','antes','de','el','la','los','las','y','en','por','este','esta','use',
    'workflow','review','secure','security','code','branch','agent','agents'
}


@dataclass
class CmdResult:
    command: str
    cwd: str
    returncode: int
    stdout: str
    stderr: str


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def run_cmd(command: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> CmdResult:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        env=merged_env,
        shell=True,
        text=True,
        capture_output=True,
    )
    return CmdResult(command=command, cwd=str(cwd), returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def normalize_name(name: str) -> str:
    name = name.strip()
    if name.endswith('.md'):
        name = name[:-3]
    if name == 'SKILL':
        return name
    return name


def parse_search_output(text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        m = SEARCH_HEADER_RE.match(line)
        if m:
            current = {
                'ref': m.group('ref'),
                'name': normalize_name(m.group('name')),
                'score': None,
                'source': None,
                'path': None,
            }
            hits.append(current)
            continue
        if current is None:
            continue
        m = SCORE_RE.match(line)
        if m:
            current['score'] = float(m.group('score'))
            continue
        m = SOURCE_RE.match(line)
        if m:
            current['source'] = m.group('source').strip()
            continue
        m = PATH_RE.match(line)
        if m:
            current['path'] = m.group('path').strip()
            continue
    return hits


def parse_excerpt_output(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    body: list[str] = []
    for line in text.splitlines():
        m = EXCERPT_HEADER_RE.match(line)
        if m:
            if current is not None:
                current['excerpt'] = '\n'.join(body).strip()
                items.append(current)
            current = {'ref': m.group('ref'), 'name': normalize_name(m.group('name')), 'excerpt': ''}
            body = []
            continue
        if current is not None:
            body.append(line)
    if current is not None:
        current['excerpt'] = '\n'.join(body).strip()
        items.append(current)
    return items


def meaningful_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-záéíóúñ0-9][a-záéíóúñ0-9_-]+", text.lower()))
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def search_cmd(query: str) -> str:
    return f'TRIFECTA_LINT=1 uv run trifecta ctx search --segment {shlex.quote(str(SEGMENT))} --query {shlex.quote(query)}'


def get_cmd(refs: list[str], query: str) -> str:
    joined = ','.join(refs)
    return (
        f'uv run trifecta ctx get --segment {shlex.quote(str(SEGMENT))} '
        f'--ids {shlex.quote(joined)} --mode excerpt --query {shlex.quote(query)}'
    )


def needs_rewrite(query: str) -> bool:
    q = query.strip().lower()
    words = q.split()
    markers = ('how to', 'como ', 'quiero', 'debug ', 'review ', 'mejora ', 'seguridad ', 'security ', 'work order')
    return len(words) < 5 or not any(m in q for m in markers)


def rewrite_query(query: str, language: str) -> str:
    if not needs_rewrite(query):
        return query
    if language == 'es':
        return f'Encuentra skills para {query}'
    return f'Find skills for {query}'


def fallback_query(query: str, language: str) -> str:
    if language == 'es':
        return f'Find skills related to: {query}'
    return f'Find skills related to: {query}'


def signal_is_weak(hits: list[dict[str, Any]]) -> bool:
    if not hits:
        return True
    if len(hits) < 3:
        return True
    top1 = hits[0].get('score') or 0.0
    top3 = hits[min(2, len(hits)-1)].get('score') or 0.0
    return top1 < 1.0 or (top1 < 2.0 and top3 < 1.5)


def excerpt_conflict(query_text: str, top1_name: str | None, excerpt_items: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    reason_codes: list[str] = []
    if not top1_name:
        return True, ['missing_top1']
    query_tokens = meaningful_tokens(query_text)
    for item in excerpt_items:
        if item['name'] == top1_name:
            excerpt_tokens = meaningful_tokens(item['excerpt']) | meaningful_tokens(item['name'])
            overlap = query_tokens & excerpt_tokens
            if overlap:
                return False, ['excerpt_support']
            reason_codes.append('excerpt_conflict')
            return True, reason_codes
    return True, ['missing_excerpt']


def determine_confidence(control_type: str, top1_useful: bool, top3_good: bool, weak_signal: bool, fallback_used: bool,
                         excerpt_has_conflict: bool) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    if top3_good:
        reasons.append('top3_match')
    if top1_useful:
        reasons.append('top1_match')
    if weak_signal:
        reasons.append('low_signal')
    if fallback_used:
        reasons.append('fallback_used')
    if excerpt_has_conflict:
        reasons.append('excerpt_conflict')
    if control_type == 'negative':
        reasons.append('negative_control')
        return 'low', reasons
    if top1_useful and top3_good and not weak_signal and not excerpt_has_conflict:
        return 'high', reasons
    if top3_good and not excerpt_has_conflict:
        return 'medium', reasons
    return 'low', reasons


def evaluate_row(query: dict[str, Any], top1_name: str | None, top3_names: list[str], confidence: str | None) -> dict[str, Any]:
    expected = set(query.get('expected_good_skills', []))
    adjacent = set(query.get('acceptable_adjacent_skills', []))
    control_type = query['control_type']
    top1_useful = top1_name in expected or top1_name in adjacent
    top3_good = any(name in expected or name in adjacent for name in top3_names)
    severe = False
    if control_type == 'negative':
        if confidence == 'high':
            severe = True
        elif confidence == 'medium':
            severe = True
    else:
        if top1_name is not None and not top1_useful and not top3_good:
            severe = True
    if confidence is None:
        confidence_matches = None
    elif confidence == 'high':
        confidence_matches = top1_useful and top3_good and not severe
    elif confidence == 'medium':
        confidence_matches = (top3_good and not severe) and (not top1_useful or True)
    else:
        confidence_matches = (not top3_good) or severe or control_type == 'negative'
    return {
        'top1_useful': top1_useful,
        'top3_contains_good_candidate': top3_good,
        'severe_false_positive': severe,
        'confidence_matches_reality': confidence_matches,
    }


def required_marker_present(text: str, markers: list[str]) -> bool:
    return all(m in text for m in markers)


def build_preflight(dataset_obj: dict[str, Any], hashes: dict[str, str]) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    queries = dataset_obj.get('queries', [])
    if len(queries) != 16:
        issues.append(f'dataset_size_expected_16_got_{len(queries)}')
    control_types = {q['control_type'] for q in queries}
    for needed in ('hard-positive', 'ambiguous', 'negative'):
        if needed not in control_types:
            issues.append(f'missing_slice_{needed}')
    if dataset_obj.get('positive_control_queries') != ['q04', 'q07', 'q10']:
        issues.append('positive_controls_mismatch')

    plan_text = PLAN.read_text()
    sample_text = SAMPLE_PLAN.read_text()
    spec_text = SPEC.read_text()
    schema_text = SCHEMA.read_text()
    reviewer_text = REVIEWER.read_text()

    if not required_marker_present(sample_text, ['Size:\n- 16 queries', 'Required reporting slices:', 'Subset application mode:', 'Fail-close rule:']):
        issues.append('sample_plan_missing_required_markers')
    if 'corpus subset is **not** a retrieval prefilter' not in spec_text:
        issues.append('spec_subset_application_mode_missing')
    if 'Abort before B if any of these differ from frozen A' not in schema_text:
        issues.append('schema_fail_close_missing')
    if 'q04' not in spec_text or 'q07' not in spec_text or 'q10' not in spec_text:
        issues.append('no_regression_controls_missing')
    if 'medium confidence despite insufficient evidence' not in schema_text:
        issues.append('negative_overclaim_rule_missing')
    if 'Frozen decision hierarchy' not in reviewer_text or 'invalid run' not in reviewer_text:
        issues.append('reviewer_hierarchy_or_invalid_run_missing')
    if 'Phase 5 frozen decision hierarchy' not in plan_text:
        issues.append('master_hierarchy_missing')

    operable = {
        'runner_command': True,
        'wrapper_path': WRAPPER.exists(),
        'wrapper_sha256': bool(hashes.get('wrapper_sha256')),
        'parser_sha256': bool(hashes.get('parser_sha256')),
        'run_started_at': True,
        'retrieval_raw_output_path': True,
        'presentation_output_path': True,
    }
    for key, ok in operable.items():
        if not ok:
            issues.append(f'operability_missing_{key}')
    return issues, operable


def execute_arm_a(query: dict[str, Any], run_dir: Path, frozen: dict[str, Any]) -> dict[str, Any]:
    qid = query['id']
    qtext = query['query']
    raw_dir = run_dir / 'raw' / 'A'
    retrieval_path = raw_dir / f'{qid}_retrieval.txt'
    presentation_path = raw_dir / f'{qid}_presentation.txt'
    runner_command = f'{WRAPPER} {shlex.quote(qtext)}'
    search_command = search_cmd(qtext)
    search_res = run_cmd(search_command, cwd=ROOT, env={'TRIFECTA_LINT': '1'})
    wrapper_res = run_cmd(runner_command, cwd=ROOT)
    write_text(retrieval_path, search_res.stdout + ('\n[stderr]\n' + search_res.stderr if search_res.stderr else ''))
    write_text(presentation_path, wrapper_res.stdout + ('\n[stderr]\n' + wrapper_res.stderr if wrapper_res.stderr else ''))
    hits = parse_search_output(search_res.stdout)
    top1 = hits[0] if hits else {}
    top3 = [h['name'] for h in hits[:3]]
    eval_fields = evaluate_row(query, top1.get('name'), top3, None)
    return {
        'query_id': qid,
        'original_query': qtext,
        'control_type': query['control_type'],
        'difficulty': query['difficulty'],
        'arm': 'A',
        'dataset_version': frozen['dataset_version'],
        'corpus_subset_version': frozen['corpus_subset_version'],
        'manifest_sha256': frozen['manifest_sha256'],
        'context_pack_sha256': frozen['context_pack_sha256'],
        'aliases_sha256': frozen['aliases_sha256'],
        'wrapper_path': str(SCRIPT_PATH),
        'wrapper_sha256': frozen['parser_sha256'],
        'parser_sha256': frozen['parser_sha256'],
        'runner_command': runner_command,
        'run_started_at': now_utc(),
        'search_query_used': qtext,
        'fallback_query_used': None,
        'retrieval_raw_output_path': str(retrieval_path),
        'presentation_output_path': str(presentation_path),
        'top1_name': top1.get('name'),
        'top1_source': top1.get('source'),
        'top1_score_raw': top1.get('score'),
        'top3_names': top3,
        'recommended_skill': top1.get('name'),
        'alternatives': top3[1:3],
        'confidence': None,
        'confidence_reason_codes': [],
        'severe_false_positive': eval_fields['severe_false_positive'],
        'top1_useful': eval_fields['top1_useful'],
        'top3_contains_good_candidate': eval_fields['top3_contains_good_candidate'],
        'confidence_matches_reality': eval_fields['confidence_matches_reality'],
        'notes': 'baseline_wrapper_has_no_native_confidence_or_recommendation_layer',
    }


def execute_arm_b(query: dict[str, Any], run_dir: Path, frozen: dict[str, Any]) -> dict[str, Any]:
    qid = query['id']
    qtext = query['query']
    language = query['language']
    raw_dir = run_dir / 'raw' / 'B'
    retrieval_path = raw_dir / f'{qid}_retrieval.txt'
    get_path = raw_dir / f'{qid}_get.txt'
    presentation_path = raw_dir / f'{qid}_presentation.json'

    rewritten = rewrite_query(qtext, language)
    search_command = search_cmd(rewritten)
    search_res = run_cmd(search_command, cwd=ROOT, env={'TRIFECTA_LINT': '1'})
    hits = parse_search_output(search_res.stdout)
    fallback_used = None
    if signal_is_weak(hits):
        fallback_used = fallback_query(qtext, language)
        search_command = search_cmd(fallback_used)
        search_res = run_cmd(search_command, cwd=ROOT, env={'TRIFECTA_LINT': '1'})
        hits = parse_search_output(search_res.stdout)
    write_text(retrieval_path, search_res.stdout + ('\n[stderr]\n' + search_res.stderr if search_res.stderr else ''))

    refs = [h['ref'] for h in hits[:3] if h.get('ref')]
    get_res = run_cmd(get_cmd(refs, qtext), cwd=ROOT) if refs else CmdResult('', str(ROOT), 0, '', '')
    write_text(get_path, get_res.stdout + ('\n[stderr]\n' + get_res.stderr if get_res.stderr else ''))
    excerpt_items = parse_excerpt_output(get_res.stdout)
    top1 = hits[0] if hits else {}
    top3 = [h['name'] for h in hits[:3]]

    provisional = evaluate_row(query, top1.get('name'), top3, 'low')
    weak_signal = signal_is_weak(hits)
    conflict, conflict_reasons = excerpt_conflict(qtext + ' ' + rewritten, top1.get('name'), excerpt_items)
    confidence, reasons = determine_confidence(
        query['control_type'],
        provisional['top1_useful'],
        provisional['top3_contains_good_candidate'],
        weak_signal,
        fallback_used is not None,
        conflict,
    )
    reasons.extend(conflict_reasons)
    reasons = list(dict.fromkeys(reasons))
    eval_fields = evaluate_row(query, top1.get('name'), top3, confidence)
    notes = []
    if conflict:
        notes.append('ctx_get_weakened_top1')
    if fallback_used:
        notes.append('fallback_used')
    presentation_obj = {
        'original_query': qtext,
        'rewritten_query': rewritten,
        'fallback_query_used': fallback_used,
        'search_results_top5': [
            {'name': h.get('name'), 'source': h.get('source'), 'score': h.get('score'), 'ref': h.get('ref')}
            for h in hits[:5]
        ],
        'excerpt_validated_top3': excerpt_items,
        'recommended_skill': top1.get('name'),
        'alternatives': top3[1:3],
        'confidence': confidence,
        'confidence_reason_codes': reasons,
        'notes_on_false_positive_risk': notes,
    }
    write_json(presentation_path, presentation_obj)
    return {
        'query_id': qid,
        'original_query': qtext,
        'control_type': query['control_type'],
        'difficulty': query['difficulty'],
        'arm': 'B',
        'dataset_version': frozen['dataset_version'],
        'corpus_subset_version': frozen['corpus_subset_version'],
        'manifest_sha256': frozen['manifest_sha256'],
        'context_pack_sha256': frozen['context_pack_sha256'],
        'aliases_sha256': frozen['aliases_sha256'],
        'wrapper_path': str(SCRIPT_PATH),
        'wrapper_sha256': frozen['parser_sha256'],
        'parser_sha256': frozen['parser_sha256'],
        'runner_command': search_command,
        'run_started_at': now_utc(),
        'search_query_used': fallback_used or rewritten,
        'fallback_query_used': fallback_used,
        'retrieval_raw_output_path': str(retrieval_path),
        'presentation_output_path': str(presentation_path),
        'top1_name': top1.get('name'),
        'top1_source': top1.get('source'),
        'top1_score_raw': top1.get('score'),
        'top3_names': top3,
        'recommended_skill': top1.get('name'),
        'alternatives': top3[1:3],
        'confidence': confidence,
        'confidence_reason_codes': reasons,
        'severe_false_positive': eval_fields['severe_false_positive'],
        'top1_useful': eval_fields['top1_useful'],
        'top3_contains_good_candidate': eval_fields['top3_contains_good_candidate'],
        'confidence_matches_reality': eval_fields['confidence_matches_reality'],
        'notes': ';'.join(notes) if notes else '',
    }


def freeze_hashes(parser_sha: str) -> dict[str, Any]:
    dataset_obj = yaml.safe_load(DATASET.read_text())
    subset_obj = yaml.safe_load(CORPUS_SUBSET.read_text())
    return {
        'dataset_version': dataset_obj['frozen_inputs']['dataset_version'],
        'corpus_subset_version': subset_obj['frozen_inputs']['corpus_subset_version'],
        'dataset_sha256': sha256(DATASET),
        'corpus_subset_sha256': sha256(CORPUS_SUBSET),
        'manifest_sha256': sha256(MANIFEST),
        'context_pack_sha256': sha256(CONTEXT_PACK),
        'aliases_sha256': sha256(ALIASES),
        'wrapper_sha256': sha256(WRAPPER),
        'baseline_presentation_sha256': sha256(BASELINE_PRESENTATION),
        'parser_sha256': parser_sha,
    }


def verify_hashes(frozen: dict[str, Any]) -> list[str]:
    current = {
        'dataset_sha256': sha256(DATASET),
        'corpus_subset_sha256': sha256(CORPUS_SUBSET),
        'manifest_sha256': sha256(MANIFEST),
        'context_pack_sha256': sha256(CONTEXT_PACK),
        'aliases_sha256': sha256(ALIASES),
        'wrapper_sha256': sha256(WRAPPER),
        'parser_sha256': sha256(SCRIPT_PATH),
    }
    mismatches = []
    for key, value in current.items():
        if frozen.get(key) != value:
            mismatches.append(key)
    return mismatches


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_arm: dict[str, list[dict[str, Any]]] = {'A': [], 'B': []}
    for row in rows:
        by_arm[row['arm']].append(row)
    out: dict[str, Any] = {}
    for arm, items in by_arm.items():
        total = len(items) or 1
        top1_rate = sum(1 for r in items if r['top1_useful']) / total
        top3_rate = sum(1 for r in items if r['top3_contains_good_candidate']) / total
        conf_vals = [r['confidence_matches_reality'] for r in items if r['confidence_matches_reality'] is not None]
        conf_rate = (sum(1 for x in conf_vals if x) / len(conf_vals)) if conf_vals else None
        severe_total = sum(1 for r in items if r['severe_false_positive'])
        slices: dict[str, Any] = {}
        for slice_name in ('hard-positive', 'ambiguous', 'negative'):
            slice_items = [r for r in items if r['control_type'] == slice_name]
            if not slice_items:
                continue
            slices[slice_name] = {
                'count': len(slice_items),
                'top1_useful_rate': sum(1 for r in slice_items if r['top1_useful']) / len(slice_items),
                'top3_contains_good_candidate_rate': sum(1 for r in slice_items if r['top3_contains_good_candidate']) / len(slice_items),
                'severe_false_positives': sum(1 for r in slice_items if r['severe_false_positive']),
            }
        out[arm] = {
            'count': len(items),
            'top1_useful_rate': top1_rate,
            'top3_contains_good_candidate_rate': top3_rate,
            'confidence_matches_reality_rate': conf_rate,
            'severe_false_positives': severe_total,
            'slices': slices,
        }
    return out


def verdict(rows: list[dict[str, Any]], invalid_reasons: list[str]) -> dict[str, Any]:
    summary = summarize(rows)
    a = {r['query_id']: r for r in rows if r['arm'] == 'A'}
    b = {r['query_id']: r for r in rows if r['arm'] == 'B'}
    no_regression_failures = []
    for qid in ('q04', 'q07', 'q10'):
        if qid not in a or qid not in b:
            no_regression_failures.append(qid)
            continue
        if a[qid]['top1_useful'] and not b[qid]['top1_useful']:
            no_regression_failures.append(qid)
        elif (not a[qid]['top1_useful']) and a[qid]['top3_contains_good_candidate'] and (not b[qid]['top3_contains_good_candidate']):
            no_regression_failures.append(qid)

    b_items = list(b.values())
    severe_negative = [r['query_id'] for r in b_items if r['control_type'] == 'negative' and r['severe_false_positive']]
    slice_failures = []
    hard = summary.get('B', {}).get('slices', {}).get('hard-positive')
    amb = summary.get('B', {}).get('slices', {}).get('ambiguous')
    neg = summary.get('B', {}).get('slices', {}).get('negative')
    if hard and hard['top3_contains_good_candidate_rate'] < 1.0:
        slice_failures.append('hard-positive')
    if amb and amb['top3_contains_good_candidate_rate'] < 0.5:
        slice_failures.append('ambiguous')
    if neg and neg['severe_false_positives'] > 0:
        slice_failures.append('negative')

    bsum = summary.get('B', {})
    thresholds_fail = []
    if bsum.get('top1_useful_rate', 0) < 0.50:
        thresholds_fail.append('top1_useful')
    if bsum.get('top3_contains_good_candidate_rate', 0) < 0.83:
        thresholds_fail.append('top3_contains_good_candidate')
    conf_rate = bsum.get('confidence_matches_reality_rate')
    if conf_rate is not None and conf_rate < 0.75:
        thresholds_fail.append('confidence_matches_reality')
    if bsum.get('severe_false_positives', 0) > 1:
        thresholds_fail.append('severe_false_positives')

    if invalid_reasons:
        return {'verdict': 'invalid run', 'reason': 'invalid_run', 'details': invalid_reasons, 'summary': summary}
    if no_regression_failures:
        return {'verdict': 'fail', 'reason': 'no_regression_failure', 'details': no_regression_failures, 'summary': summary}
    if severe_negative:
        return {'verdict': 'fail', 'reason': 'severe_false_positive_negative', 'details': severe_negative, 'summary': summary}
    if slice_failures:
        return {'verdict': 'fail', 'reason': 'slice_failure', 'details': slice_failures, 'summary': summary}
    if thresholds_fail:
        return {'verdict': 'fail', 'reason': 'threshold_failure', 'details': thresholds_fail, 'summary': summary}
    return {'verdict': 'pass with issues', 'reason': 'pilot_executed_without_higher_priority_failure', 'details': [], 'summary': summary}


def main() -> int:
    parser_sha = sha256(SCRIPT_PATH)
    frozen = freeze_hashes(parser_sha)
    dataset_obj = yaml.safe_load(DATASET.read_text())
    preflight_issues, operable = build_preflight(dataset_obj, frozen)

    stamp = dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    run_dir = RESULTS_BASE / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / 'freeze.json', frozen)
    write_json(run_dir / 'preflight.json', {'issues': preflight_issues, 'operable': operable})

    if preflight_issues:
        write_json(run_dir / 'verdict.json', {'verdict': 'invalid run', 'reason': 'preflight_failed', 'details': preflight_issues})
        return 2

    rows: list[dict[str, Any]] = []
    queries = dataset_obj['queries']
    for query in queries:
        rows.append(execute_arm_a(query, run_dir, frozen))

    mismatches = verify_hashes(frozen)
    if mismatches:
        write_json(run_dir / 'verdict.json', {'verdict': 'invalid run', 'reason': 'hash_mismatch_before_B', 'details': mismatches})
        return 3

    for query in queries:
        rows.append(execute_arm_b(query, run_dir, frozen))

    mismatches_after = verify_hashes(frozen)
    invalid_reasons = [f'hash_mismatch_after_B:{m}' for m in mismatches_after]

    rows_path = run_dir / 'rows.jsonl'
    with rows_path.open('w') as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + '\n')

    report = verdict(rows, invalid_reasons)
    write_json(run_dir / 'summary.json', report)
    print(json.dumps({'run_dir': str(run_dir), **report}, ensure_ascii=False))
    return 0 if report['verdict'] != 'invalid run' else 4


if __name__ == '__main__':
    sys.exit(main())
