"""Backup portátil das camadas e evidências, antes da expiração dos recursos gratuitos."""
from pathlib import Path
import argparse
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def export():
    data = ROOT / "data"
    latest = json.loads((data / "cloud_latest.json").read_text(encoding="utf-8"))
    output = data / f"cloud_artifacts_{latest['run_id']}.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for directory in ("bronze", "silver", "gold", "audit", "cloud_audit", "console", "streaming", "monitor"):
            for path in sorted((data / directory).rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(ROOT).as_posix())
        for name in ("latest.json", "cloud_latest.json"):
            path = data / name
            archive.write(path, path.relative_to(ROOT).as_posix())
        proof = data / "cloud_failure_proof.json"
        if proof.exists():
            archive.write(proof, proof.relative_to(ROOT).as_posix())
        pointer = data / "streaming_latest.json"
        if pointer.exists():
            archive.write(pointer, pointer.relative_to(ROOT).as_posix())
        # O histórico é exportável; o tópico privado em config.json fica de fora.
        for name in ("delivery_history.json", "cloud_alert_proof.json", "outbox.sqlite"):
            path = data / "alerts" / name
            if path.exists():
                archive.write(path, path.relative_to(ROOT).as_posix())
    print(output, flush=True)
    return output


def export_streaming():
    data = ROOT / "data"
    latest = json.loads((data / "streaming_latest.json").read_text(encoding="utf-8"))
    directory = data / "streaming" / latest["run_id"]
    output = data / f"streaming_artifacts_{latest['run_id']}.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
        audit = json.loads((directory / "audit.json").read_text(encoding="utf-8"))
        baseline = Path(audit["baseline"])
        archive.write(baseline, (directory.relative_to(ROOT) / "baseline_oficial.csv").as_posix())
        pointer = data / "streaming_latest.json"
        archive.write(pointer, pointer.relative_to(ROOT).as_posix())
    print(output, flush=True)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streaming", action="store_true", help="Exportar somente a última demonstração de streaming")
    args = parser.parse_args()
    export_streaming() if args.streaming else export()
