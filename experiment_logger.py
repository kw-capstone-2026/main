"""
experiment_logger.py
---------------------
위치: 프로젝트 루트 (main.py와 같은 위치)

모든 실험 결과를 CSV와 마크다운 보고서로 자동 저장합니다.
점수가 좋든 나쁘든 전부 기록하여 보고서 작성에 활용합니다.

사용법:
    from experiment_logger import ExperimentLogger
    logger = ExperimentLogger()
    logger.log(
        exp_id="EXP_001",
        description="유동인구 시간대별 변수 추가",
        features_used=["store_age", "local_competitors", "peak_hour_pop"],
        hyperparams={"n_estimators": 100, "max_depth": 4, "learning_rate": 0.05, "reg_lambda": 5},
        metrics={"auc": 0.74, "accuracy": 0.81},
        data_sources=["DS1", "DS3", "DS2-VwsmTrdarFlpopQq"],
        notes="피크 시간대 유동인구 추가 시 AUC 0.77→0.79 개선"
    )
    logger.print_summary()   # 전체 실험 비교표 출력
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


class ExperimentLogger:

    def __init__(self, base_dir: str = "experiments"):
        self.base_dir = Path(base_dir)
        self.reports_dir = self.base_dir / "reports"
        self.log_path = self.base_dir / "experiment_log.csv"

        self.base_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8-sig") as f:
                csv.DictWriter(f, fieldnames=self._fields()).writeheader()
            print(f"[Logger] 실험 로그 초기화: {self.log_path}")

    def _fields(self):
        return [
            "exp_id", "timestamp", "description",
            "n_estimators", "max_depth", "learning_rate", "reg_lambda", "scale_pos_weight",
            "auc", "accuracy",
            "n_features", "features_used",
            "data_sources", "train_samples", "test_samples",
            "notes"
        ]

    def log(
        self,
        exp_id: str,
        description: str,
        features_used: list,
        hyperparams: dict,
        metrics: dict,
        data_sources: list = None,
        train_samples: int = None,
        test_samples: int = None,
        notes: str = "",
    ) -> dict:
        """
        실험 결과를 CSV 로그와 마크다운 보고서로 동시 저장합니다.
        Returns: 저장된 row dict
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hp = hyperparams or {}
        mt = metrics or {}

        row = {
            "exp_id": exp_id,
            "timestamp": ts,
            "description": description,
            "n_estimators": hp.get("n_estimators", ""),
            "max_depth": hp.get("max_depth", ""),
            "learning_rate": hp.get("learning_rate", ""),
            "reg_lambda": hp.get("reg_lambda", ""),
            "scale_pos_weight": hp.get("scale_pos_weight", "auto"),
            "auc": mt.get("auc", ""),
            "accuracy": mt.get("accuracy", ""),
            "n_features": len(features_used),
            "features_used": json.dumps(features_used, ensure_ascii=False),
            "data_sources": json.dumps(data_sources or [], ensure_ascii=False),
            "train_samples": train_samples or "",
            "test_samples": test_samples or "",
            "notes": notes,
        }

        # 1) CSV 추가
        with open(self.log_path, "a", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=self._fields()).writerow(row)

        # 2) 마크다운 보고서 생성
        md_path = self.reports_dir / f"{exp_id}.md"
        self._write_report(md_path, row, features_used, hp, mt, data_sources, notes)

        auc_val = mt.get("auc")
        auc_str = f"{auc_val:.4f}" if isinstance(auc_val, float) else "N/A"
        print(f"[Logger] {exp_id} 저장 완료 | AUC: {auc_str} | 보고서: {md_path}")
        return row

    def _write_report(self, path, row, features_used, hp, mt, data_sources, notes):
        hp = hp or {}
        mt = mt or {}
        auc_val = mt.get("auc")
        acc_val = mt.get("accuracy")
        auc = f"{auc_val:.4f}" if isinstance(auc_val, float) else "N/A"
        acc = f"{acc_val:.4f}" if isinstance(acc_val, float) else "N/A"

        lines = [
            f"# {row['exp_id']} — {row['description']}",
            "",
            f"> **실험 일시**: {row['timestamp']}",
            "",
            "---",
            "",
            "## 개요",
            "",
            row["description"],
            "",
            "## 사용 데이터 소스",
            "",
        ]
        for ds in (data_sources or []):
            lines.append(f"- {ds}")

        lines += [
            "",
            "## 하이퍼파라미터",
            "",
            "| 파라미터 | 값 | 비고 |",
            "|---|---|---|",
            f"| n_estimators | {hp.get('n_estimators', '-')} | 트리 개수 |",
            f"| max_depth | {hp.get('max_depth', '-')} | 트리 최대 깊이 |",
            f"| learning_rate | {hp.get('learning_rate', '-')} | 학습률 |",
            f"| reg_lambda | {hp.get('reg_lambda', '-')} | L2 규제 |",
            f"| scale_pos_weight | auto | 영업수/폐업수 비율 자동 적용 |",
            "",
            "## 학습에 사용된 피처",
            "",
            f"총 **{len(features_used)}개**",
            "",
        ]
        for feat in features_used:
            lines.append(f"- `{feat}`")

        lines += [
            "",
            "## 평가 결과",
            "",
            "| 지표 | 값 | 기준 |",
            "|---|---|---|",
            f"| **AUC** | **{auc}** | 0.5=찍기, 1.0=완벽, 베이스라인≈0.77 |",
            f"| Accuracy | {acc} | 클래스 불균형 존재하므로 참고용 |",
            f"| 학습 샘플 | {row.get('train_samples', '-')} | |",
            f"| 테스트 샘플 | {row.get('test_samples', '-')} | |",
            "",
            "## 분석 및 비고",
            "",
            notes if notes else "(없음)",
            "",
            "---",
            "",
            "*이 보고서는 `experiment_logger.py`에 의해 자동 생성되었습니다.*",
        ]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def print_summary(self):
        """현재까지의 모든 실험 비교표를 콘솔에 출력합니다."""
        if not self.log_path.exists():
            print("[Logger] 기록된 실험이 없습니다.")
            return

        print("\n" + "=" * 74)
        print(f"{'실험ID':<10} {'AUC':>6} {'ACC':>6} {'피처':>4}  {'설명'}")
        print("-" * 74)

        rows = []
        with open(self.log_path, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            try:
                auc = f"{float(row['auc']):.4f}"
            except (ValueError, KeyError):
                auc = "  N/A"
            try:
                acc = f"{float(row['accuracy']):.4f}"
            except (ValueError, KeyError):
                acc = "  N/A"
            nf = row.get("n_features", "-")
            desc = row["description"][:44]
            print(f"{row['exp_id']:<10} {auc:>6} {acc:>6} {nf:>4}  {desc}")

        valid = [r for r in rows if r.get("auc")]
        if valid:
            best = max(valid, key=lambda r: float(r["auc"]) if r["auc"] else 0)
            print("-" * 74)
            print(f"  ★ 최고 AUC: {best['exp_id']} ({float(best['auc']):.4f}) — {best['description'][:40]}")
        print("=" * 74 + "\n")
