"""Empacota somente código e referências necessárias, sem credenciais ou dados de alunos."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package():
    files = [ROOT / "requirements.txt", ROOT / "README.md", *sorted((ROOT / "src").glob("*.py")),
             *sorted((ROOT / "src").glob("*.sh")),
             *sorted((ROOT / "tests").glob("*.py"))]
    files += [ROOT / "referencias" / name for name in (
        "IBGE_DTB_2023.zip", "IBGE_DTB_2024.zip", "IBGE_estados.json",
        "inep_resultados_e_metas_municipios_2024.xlsx", "inep_resultados_e_metas_ufs_2024.xlsx",
        "inep_microdados_2024/TS_MUNICIPIO_2024.csv")]
    output = ROOT / "data" / "cloudshell_code.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(output)
    return output


if __name__ == "__main__":
    package()
