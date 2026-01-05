bs_fp_current += 1

    if b['predicted'] != c['predicted'] or b['selected_by'] != c['selected_by']:
        rows.append({
            'task_id': task_id,
            'task': b['task'],
            'expected': expected,
            'baseline_predicted': b_pred,
            'current_predicted': c_pred,
            'transition': f"{b['selected_by']}->{c['selected_by']}",
            'was_fp_before': expected != 'fallback' and b_pred != expected,
            'is_false_fallback_now': expected != 'fallback' and c_pred == 'fallback',
        })

summary = {
    'fp_baseline': fp_baseline,
    'fp_current': fp_current,
    'fp_reduction': fp_baseline - fp_current,
    'fallback_baseline': fallback_baseline,
    'fallback_current': fallback_current,
    'fallback_increase': fallback_current - fallback_baseline,
    'false_fallback_current': false_fallback,
    'net_impact': (fp_baseline - fp_current) - false_fallback,
    'observability_fp_baseline': obs_fp_baseline,
    'observability_fp_current': obs_fp_current,
}

Path('tmp_plan_test/t9_3_6_clamp_delta.json').write_text(json.dumps({'rows': rows, 'summary': summary}, indent=2))
PY
```
