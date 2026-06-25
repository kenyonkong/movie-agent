import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.evaluation.catalog import (
    CatalogIndex,
)
from app.evaluation.metrics import (
    aggregate_config_metrics,
    evaluate_run,
)
from app.evaluation.models import (
    EvaluationConfig,
    EvaluationQuery,
    EvaluationRun,
)
from app.evaluation.runner import (
    EvaluationPipeline,
)


DEFAULT_EVAL_DIR = (
    settings.backend_dir
    / "eval"
    / "end_to_end"
)


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        path.write_text(
            "",
            encoding="utf-8",
        )
        return

    fieldnames: list[str] = []

    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def format_metric(
    value: Any,
) -> str:
    if value is None:
        return "—"

    if isinstance(value, float):
        return f"{value:.4f}"

    return str(value)


def write_markdown_report(
    path: Path,
    summaries: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
) -> None:
    lines: list[str] = [
        "# Movie Agent End-to-End Evaluation",
        "",
        "Generated automatically by Day 17 evaluation.",
        "",
        "## Configuration Summary",
        "",
        "| Configuration | Hit@K | Precision@K | Recall@K | MRR | nDCG@K | Constraint Accuracy | Diversity | Novelty | P50 Latency | P95 Latency | Fallback Rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for summary in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(
                        summary[
                            "config_name"
                        ]
                    ),
                    format_metric(
                        summary.get(
                            "hit_at_k"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "precision_at_k"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "recall_at_k"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "reciprocal_rank"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "ndcg_at_k"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "constraint_check_accuracy"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "intra_list_diversity"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "average_catalog_novelty"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "latency_p50_ms"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "latency_p95_ms"
                        )
                    ),
                    format_metric(
                        summary.get(
                            "fallback_rate"
                        )
                    ),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Per-Query Results",
            "",
            "| Configuration | Query | Hit@K | MRR | nDCG@K | Constraint Accuracy | Diversity | Latency | Error |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )

    for row in metric_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(
                        row[
                            "config_name"
                        ]
                    ),
                    str(
                        row["query_id"]
                    ),
                    format_metric(
                        row.get(
                            "hit_at_k"
                        )
                    ),
                    format_metric(
                        row.get(
                            "reciprocal_rank"
                        )
                    ),
                    format_metric(
                        row.get(
                            "ndcg_at_k"
                        )
                    ),
                    format_metric(
                        row.get(
                            "constraint_check_accuracy"
                        )
                    ),
                    format_metric(
                        row.get(
                            "intra_list_diversity"
                        )
                    ),
                    format_metric(
                        row.get(
                            "latency_ms"
                        )
                    ),
                    str(
                        row.get("error")
                        or ""
                    ).replace(
                        "|",
                        "/",
                    ),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- Curated relevant-title lists are incomplete and should be treated as smoke-test labels.",
            "- nDCG is most meaningful after the pooled candidates have been manually graded.",
            "- Catalog novelty is a popularity-based proxy, not a direct measure of user value.",
            "- LLM configurations should be compared over multiple runs before making strong claims about stability.",
            "",
        ]
    )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Movie Agent end-to-end evaluation."
        )
    )

    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=DEFAULT_EVAL_DIR,
    )

    parser.add_argument(
        "--config",
        action="append",
        help=(
            "Run only a named configuration. "
            "Can be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--limit-queries",
        type=int,
        default=None,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    query_path = (
        args.eval_dir
        / "queries.json"
    )

    config_path = (
        args.eval_dir
        / "configurations.json"
    )

    judgment_path = (
        args.eval_dir
        / "judgments.json"
    )

    queries = [
        EvaluationQuery(**item)
        for item in load_json(
            query_path
        )
    ]

    configs = [
        EvaluationConfig(**item)
        for item in load_json(
            config_path
        )
        if item.get(
            "enabled",
            True,
        )
    ]

    if args.config:
        requested_configs = set(
            args.config
        )

        configs = [
            config
            for config in configs
            if config.name
            in requested_configs
        ]

    if args.limit_queries is not None:
        queries = queries[
            : args.limit_queries
        ]

    judgments: dict[
        str,
        dict[str, int],
    ] = (
        load_json(judgment_path)
        if judgment_path.exists()
        else {}
    )

    catalog = CatalogIndex(
        settings.movie_documents_path
    )

    print(
        f"Catalog movies: "
        f"{catalog.count:,}"
    )

    print(
        f"Queries: {len(queries)}"
    )

    print(
        f"Configurations: "
        f"{len(configs)}"
    )

    runs: list[EvaluationRun] = []

    for config in configs:
        print("\n" + "=" * 100)
        print(
            f"Preparing configuration: "
            f"{config.name}"
        )

        try:
            pipeline = EvaluationPipeline(
                config=config,
                catalog=catalog,
            )
        except Exception as error:
            print(
                f"Could not initialize "
                f"{config.name}: {error}"
            )

            for query in queries:
                runs.append(
                    EvaluationRun(
                        config_name=(
                            config.name
                        ),
                        query_id=query.id,
                        query=query.query,
                        retrieval_query="",
                        embedding_identifier=(
                            f"{config.embedding_provider}:"
                            f"{config.embedding_model}"
                        ),
                        latency_ms=0.0,
                        results=[],
                        error=(
                            f"{type(error).__name__}: "
                            f"{error}"
                        ),
                    )
                )

            continue

        for query in queries:
            print(
                f"\n[{config.name}] "
                f"{query.id}"
            )

            try:
                run = pipeline.run(query)
                runs.append(run)

                print(
                    f"Latency: "
                    f"{run.latency_ms:.2f} ms"
                )

                print(
                    "Results: "
                    + ", ".join(
                        movie.title
                        for movie
                        in run.results
                    )
                )

            except Exception as error:
                print(
                    f"Failed: {error}"
                )

                runs.append(
                    EvaluationRun(
                        config_name=(
                            config.name
                        ),
                        query_id=query.id,
                        query=query.query,
                        retrieval_query="",
                        embedding_identifier=(
                            pipeline
                            .embedding_service
                            .model_identifier
                        ),
                        latency_ms=0.0,
                        results=[],
                        error=(
                            f"{type(error).__name__}: "
                            f"{error}"
                        ),
                    )
                )

    query_by_id = {
        query.id: query
        for query in queries
    }

    metric_rows: list[
        dict[str, Any]
    ] = []

    for run in runs:
        query = query_by_id[
            run.query_id
        ]

        query_judgments = (
            judgments.get(
                run.query_id,
                {},
            )
        )

        metric_rows.append(
            evaluate_run(
                run=run,
                query=query,
                judgments=(
                    query_judgments
                ),
            )
        )

    summaries = aggregate_config_metrics(
        metric_rows
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
        args.eval_dir
        / "reports"
        / timestamp
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    runs_path = (
        output_dir / "runs.json"
    )

    metrics_path = (
        output_dir
        / "per_query_metrics.csv"
    )

    summary_path = (
        output_dir
        / "summary.csv"
    )

    report_path = (
        output_dir
        / "report.md"
    )

    runs_path.write_text(
        json.dumps(
            [
                run.model_dump()
                for run in runs
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    write_csv(
        metrics_path,
        metric_rows,
    )

    write_csv(
        summary_path,
        summaries,
    )

    write_markdown_report(
        report_path,
        summaries,
        metric_rows,
    )

    print("\n" + "=" * 100)
    print("Evaluation complete.")
    print(f"Runs: {runs_path}")
    print(f"Metrics: {metrics_path}")
    print(f"Summary: {summary_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()