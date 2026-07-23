from __future__ import annotations

from pathlib import Path

from eval.runners.models import BenchmarkResult


def write_html_report(result: BenchmarkResult, output_path: Path) -> Path:
    fields_rows = ""
    for name, metrics in result.field_metrics.items():
        fields_rows += f"""
        <tr>
          <td>{name}</td>
          <td>{metrics.accuracy:.1%}</td>
          <td>{metrics.precision:.1%}</td>
          <td>{metrics.recall:.1%}</td>
          <td>{metrics.f1:.1%}</td>
          <td>{metrics.correct}/{metrics.total}</td>
        </tr>"""

    per_call_rows = ""
    for row in result.per_call:
        match_cells = "".join(
            f'<td class="{"ok" if row["matches"].get(f) else "bad"}">'
            f'{"✓" if row["matches"].get(f) else "✗"}</td>'
            for f in result.field_metrics.keys()
        )
        per_call_rows += f"""
        <tr>
          <td>{row.get("call_id") or "—"}</td>
          {match_cells}
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Operyx Eval Report — {result.dataset_name}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    h1 {{ color: #4338ca; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 0.5rem 0.75rem; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .ok {{ color: #15803d; font-weight: 600; }}
    .bad {{ color: #b91c1c; font-weight: 600; }}
    .meta {{ color: #6b7280; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Evaluation Report</h1>
  <p class="meta">
    Run ID: {result.run_id}<br />
    Dataset: {result.dataset_name}<br />
    Prompt: {result.prompt_version} · STT: {result.stt_provider} · LLM: {result.llm_provider}<br />
    Ran at: {result.ran_at.isoformat()} UTC
  </p>

  <h2>Summary</h2>
  <ul>
    <li>Total samples: {result.summary["total"]}</li>
    <li>All fields correct: {result.summary["matched_all_fields"]}</li>
    <li>Macro accuracy: {result.summary["macro_accuracy"]:.1%}</li>
  </ul>

  <h2>Per-field Metrics</h2>
  <table>
    <thead>
      <tr>
        <th>Field</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>Correct</th>
      </tr>
    </thead>
    <tbody>{fields_rows}</tbody>
  </table>

  <h2>Per-call Breakdown</h2>
  <table>
    <thead>
      <tr>
        <th>Call ID</th>
        {"".join(f"<th>{f}</th>" for f in result.field_metrics.keys())}
      </tr>
    </thead>
    <tbody>{per_call_rows}</tbody>
  </table>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
