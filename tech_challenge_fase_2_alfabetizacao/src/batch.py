"""Batch: Bronze pública -> Silver Parquet -> Gold 2024, local ou no Cloud Shell."""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import socket
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import duckdb

from ingest import ROOT, TABLES, digest, download, new_run_id, now, write_json


def ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def xlsx_rows(path: Path) -> list[dict[str, str]]:
    """Leitura dos valores originais das referências; não altera as planilhas."""
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(item.itertext()) for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", ns)]
        out = []
        for row in ET.fromstring(archive.read("xl/worksheets/sheet1.xml")).findall(".//s:row", ns):
            values = {}
            for cell in row.findall("s:c", ns):
                column = "".join(c for c in cell.attrib["r"] if c.isalpha())
                v = cell.find("s:v", ns)
                if v is not None:
                    text = v.text or ""
                    values[column] = strings[int(text)] if cell.get("t") == "s" else text
                elif cell.get("t") == "inlineStr":
                    values[column] = "".join(cell.itertext())
            out.append(values)
        return out


def number(value: str | None) -> float | None:
    value = (value or "").strip()
    if value in ("", "-"):
        return None
    return float(value.replace(">", "").replace("%", "").replace(",", ".").strip())


def reference_data() -> tuple[list[tuple], set[str], set[str], list[tuple]]:
    ref = ROOT / "referencias"
    ufs = {str(row["id"]): row for row in json.loads((ref / "IBGE_estados.json").read_text(encoding="utf-8"))}
    territories = []
    ns = {"t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0"}
    for year in (2023, 2024):
        with zipfile.ZipFile(ref / f"IBGE_DTB_{year}.zip") as archive:
            member = next(n for n in archive.namelist() if "MUNICIPIO" in n and n.endswith(".ods"))
            with zipfile.ZipFile(io.BytesIO(archive.read(member))) as ods:
                tree = ET.fromstring(ods.read("content.xml"))
        for row in tree.findall(".//t:table-row", ns):
            values = []
            for cell in row:
                if cell.tag.endswith(("table-cell", "covered-table-cell")):
                    copies = min(int(cell.get("{" + ns["t"] + "}number-columns-repeated", "1")), 12)
                    values.extend([" ".join(cell.itertext())] * copies)
            if len(values) > 8 and len(values[7]) == 7 and values[7].isdigit():
                territories.append((year, values[7], values[8], values[0], ufs[values[0]]["sigla"], values[1]))

    municipalities = {}
    with (ref / "inep_microdados_2024" / "TS_MUNICIPIO_2024.csv").open(encoding="latin1", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["TP_SERIE"] == "2" and row["ID_TIPO_REDE"] == "3":
                municipalities[row["CO_MUNICIPIO"]] = row
    rows = xlsx_rows(ref / "inep_resultados_e_metas_municipios_2024.xlsx")
    metas = {str(int(row["D"])): row for row in rows if row.get("A") == "2024" and row.get("D")}
    missing = set(municipalities) - set(metas)
    empty = {code for code in municipalities.keys() & metas.keys() if number(metas[code].get("I")) is None}

    references = []
    for code, row in metas.items():
        for offset, year in enumerate(range(2024, 2031)):
            text = row.get(chr(ord("I") + offset), "")
            references.append(("MUNICIPIO", code, year, text, ">" if ">" in text else ">=", number(text), number(row.get("H"))))
    for row in xlsx_rows(ref / "inep_resultados_e_metas_ufs_2024.xlsx"):
        if row.get("A") != "2024":
            continue
        level, code = ("BRASIL", "BR") if row.get("D") == "Brasil" else ("UF", row["C"])
        for offset, year in enumerate(range(2024, 2031)):
            text = row.get(chr(ord("H") + offset), "")
            references.append((level, code, year, text, ">" if ">" in text else ">=", number(text), number(row.get("G"))))
    return territories, missing, empty, references


def run(bronze: Path | None = None, inject_failure: bool = False) -> dict:
    run_id = new_run_id()
    audit = {"run_id": run_id, "started_at": now(), "status": "RUNNING",
             "execution": "GOOGLE_CLOUD_SHELL" if os.environ.get("CLOUD_SHELL") == "true" else "LOCAL",
             "hostname": socket.gethostname(),
             "paid_cloud_services": False, "checks": [], "counts": {}}
    audit_path = ROOT / "data" / "audit" / f"{run_id}.json"
    started = time.monotonic()

    def check(name: str, bad: int, severity: str = "BLOCK") -> None:
        audit["checks"].append({"name": name, "violations": bad, "severity": severity,
                                "status": "PASS" if bad == 0 else "FAIL" if severity == "BLOCK" else "WARNING"})
        write_json(audit_path, audit)
        if bad and severity == "BLOCK":
            raise ValueError(f"Qualidade bloqueante: {name} ({bad} ocorrências)")

    con = duckdb.connect()
    con.execute("SET memory_limit='512MB'; SET threads=2")
    temp_dir = ROOT / 'data' / 'tmp' / run_id
    temp_dir.mkdir(parents=True, exist_ok=False)
    con.execute(f"SET temp_directory={literal(temp_dir)}")
    try:
        bronze = bronze.resolve() if bronze else download()
        manifest = json.loads((bronze / "manifest.json").read_text(encoding="utf-8"))
        audit["bronze_run_id"] = manifest["run_id"]
        check("bronze_completa", int(manifest["status"] != "SUCCESS" or set(manifest["tables"]) != set(TABLES)))
        types = {"INTEGER": "BIGINT", "FLOAT": "DOUBLE", "STRING": "VARCHAR", "BOOLEAN": "BOOLEAN"}
        keys = {
            "municipio": ["ano", "id_municipio", "serie", "rede"], "uf": ["ano", "sigla_uf", "serie", "rede"],
            "alunos": ["ano", "id_municipio", "id_escola", "id_aluno", "serie", "rede"],
            "meta_alfabetizacao_municipio": ["ano", "id_municipio", "rede"],
            "meta_alfabetizacao_uf": ["ano", "sigla_uf", "rede"], "meta_alfabetizacao_brasil": ["ano", "rede"],
            "dicionario": ["id_tabela", "nome_coluna", "chave"],
        }
        for table in TABLES:
            entry = manifest["tables"][table]
            path = bronze / entry["file"]
            check(f"hash_{table}", int(digest(path) != entry["sha256"]))
            fields = json.loads((bronze / f"{table}.metadata.json").read_text(encoding="utf-8"))["schema"]["fields"]
            con.execute(f"CREATE VIEW {ident('input_' + table)} AS SELECT * FROM read_csv({literal(path)}, header=true, all_varchar=true, nullstr='\\N')")
            columns = ",".join(f"CAST({ident(f['name'])} AS {types[f['type']]}) AS {ident(f['name'])}" for f in fields)
            con.execute(f"CREATE TABLE {ident(table)} AS SELECT {columns} FROM {ident('input_' + table)}")
            count = con.execute(f"SELECT count(*) FROM {ident(table)}").fetchone()[0]
            audit["counts"][table] = count
            check(f"contagem_{table}", abs(count - entry["rows"]))
            columns_key = ",".join(map(ident, keys[table]))
            null_key = " OR ".join(f"{ident(k)} IS NULL" for k in keys[table])
            check(f"chave_nula_{table}", con.execute(f"SELECT count(*) FROM {ident(table)} WHERE {null_key}").fetchone()[0])
            check(f"chave_duplicada_{table}", con.execute(f"SELECT count(*) FROM (SELECT {columns_key} FROM {ident(table)} GROUP BY {columns_key} HAVING count(*)>1)").fetchone()[0])
            for f in fields:
                col = f["name"]
                if col.startswith(("taxa_", "meta_alfabetizacao_", "proporcao_aluno_")) or col == "percentual_participacao":
                    check(f"percentual_{table}_{col}", con.execute(f"SELECT count(*) FROM {ident(table)} WHERE {ident(col)} IS NOT NULL AND (NOT isfinite({ident(col)}) OR {ident(col)}<0 OR {ident(col)}>100)").fetchone()[0])
            print(f"[silver] {table}: {count:,}", flush=True)

        for table in ("municipio", "uf", "alunos"):
            for column in ("rede", "serie"):
                bad = con.execute(f"SELECT count(*) FROM {table} a WHERE NOT EXISTS (SELECT 1 FROM dicionario d WHERE d.id_tabela={literal(table)} AND d.nome_coluna={literal(column)} AND d.chave=a.{column})").fetchone()[0]
                check(f"dominio_{table}_{column}", bad)
        check("alunos_dominios", con.execute("SELECT count(*) FROM alunos WHERE presenca IS NULL OR presenca NOT IN ('0','1') OR preenchimento_caderno IS NULL OR preenchimento_caderno NOT IN ('0','1') OR alfabetizado IS NULL OR alfabetizado NOT IN ('0','1')").fetchone()[0])
        check("alunos_avaliados_validos", con.execute("SELECT count(*) FROM alunos WHERE presenca='1' AND preenchimento_caderno='1' AND (peso_aluno IS NULL OR NOT isfinite(peso_aluno) OR peso_aluno<=0 OR proficiencia IS NULL OR NOT isfinite(proficiencia))").fetchone()[0])
        check("alunos_classificacao_corte", con.execute("SELECT count(*) FROM alunos WHERE presenca='1' AND preenchimento_caderno='1' AND CAST(alfabetizado AS INTEGER) <> CASE WHEN proficiencia>=743 THEN 1 ELSE 0 END").fetchone()[0])
        for table, expected in (("meta_alfabetizacao_municipio", "Municipal"), ("meta_alfabetizacao_uf", "Pública"), ("meta_alfabetizacao_brasil", "Pública")):
            check(f"rede_{table}", con.execute(f"SELECT count(*) FROM {table} WHERE rede <> {literal(expected)}").fetchone()[0])
        territories, missing, empty, references = reference_data()
        con.execute("CREATE TABLE territorio(ano BIGINT,id_municipio VARCHAR,nome_municipio VARCHAR,id_uf VARCHAR,sigla_uf VARCHAR,nome_uf VARCHAR)")
        con.executemany("INSERT INTO territorio VALUES (?,?,?,?,?,?)", territories)
        for table in ("municipio", "alunos", "meta_alfabetizacao_municipio"):
            check(f"territorio_{table}", con.execute(f"SELECT count(*) FROM {table} r ANTI JOIN territorio t USING(ano,id_municipio)").fetchone()[0])
        con.execute("CREATE TABLE referencia_publicacao(nivel VARCHAR,territorio VARCHAR,ano_meta BIGINT,texto_original VARCHAR,operador VARCHAR,meta_numerica DOUBLE,resultado_original DOUBLE)")
        con.executemany("INSERT INTO referencia_publicacao VALUES (?,?,?,?,?,?,?)", references)
        con.execute("CREATE TABLE faltas_conhecidas(id_municipio VARCHAR, tipo VARCHAR)")
        con.executemany("INSERT INTO faltas_conhecidas VALUES (?,?)", [(code,"SEM_REGISTRO") for code in sorted(missing)] + [(code,"META_NULA") for code in sorted(empty)])

        selects = []
        for source, level, territory in (("municipio", "MUNICIPIO", "id_municipio"), ("uf", "UF", "sigla_uf"), ("brasil", "BRASIL", "'BR'")):
            for year in range(2024, 2031):
                selects.append(f"SELECT {literal(level)} AS nivel, {territory} AS territorio, ano AS ano_referencia, rede, {year} AS ano_meta, meta_alfabetizacao_{year} AS meta_percentual FROM meta_alfabetizacao_{source}")
        con.execute("CREATE TABLE metas_anuais AS " + " UNION ALL ".join(selects))

        con.execute("""CREATE TABLE comparacao_municipal_2024 AS
            SELECT r.id_municipio,t.nome_municipio,t.sigla_uf,r.ano,'Municipal' AS rede,
              r.taxa_alfabetizacao AS resultado_agregado,m.taxa_alfabetizacao AS resultado_publicado,
              m.meta_alfabetizacao_2024,m.meta_alfabetizacao_2030,
              m.taxa_alfabetizacao-m.meta_alfabetizacao_2024 AS saldo_meta_pp,
              CASE WHEN m.id_municipio IS NULL THEN 'Sem registro de meta'
                   WHEN m.meta_alfabetizacao_2024 IS NULL THEN 'Meta 2024 ausente'
                   WHEN m.taxa_alfabetizacao IS NULL THEN 'Resultado publicado ausente'
                   WHEN m.taxa_alfabetizacao>=m.meta_alfabetizacao_2024 THEN 'Atingiu'
                   ELSE 'Não atingiu' END AS situacao,
              m.id_municipio IS NOT NULL AS tem_registro_meta,'OFICIAL' AS origem
            FROM municipio r JOIN territorio t USING(ano,id_municipio)
            LEFT JOIN meta_alfabetizacao_municipio m ON r.ano=m.ano AND r.id_municipio=m.id_municipio AND m.rede='Municipal'
            WHERE r.ano=2024 AND r.serie='2' AND r.rede='3'""")
        check("cardinalidade_municipal", abs(con.execute("SELECT count(*) FROM comparacao_municipal_2024").fetchone()[0] - con.execute("SELECT count(*) FROM municipio WHERE ano=2024 AND serie='2' AND rede='3'").fetchone()[0]))
        check("nova_falta_meta", con.execute("""SELECT count(*) FROM comparacao_municipal_2024 c WHERE
            (NOT tem_registro_meta AND NOT EXISTS (SELECT 1 FROM faltas_conhecidas f WHERE f.id_municipio=c.id_municipio AND f.tipo='SEM_REGISTRO')) OR
            (tem_registro_meta AND meta_alfabetizacao_2024 IS NULL AND NOT EXISTS (SELECT 1 FROM faltas_conhecidas f WHERE f.id_municipio=c.id_municipio AND f.tipo='META_NULA'))""").fetchone()[0])
        check("metas_ausentes_conhecidas", con.execute("SELECT count(*) FROM comparacao_municipal_2024 WHERE NOT tem_registro_meta OR meta_alfabetizacao_2024 IS NULL").fetchone()[0], "WARN")

        for level, table, territory in (("UF", "uf", "sigla_uf"), ("BRASIL", "brasil", "'BR'")):
            con.execute(f"""CREATE TABLE comparacao_{table}_2024 AS SELECT {territory} AS territorio,m.ano,m.rede,
                m.taxa_alfabetizacao AS resultado_publicado,m.meta_alfabetizacao_2024,m.meta_alfabetizacao_2030,
                p.texto_original AS meta_2024_texto_original,p.operador AS meta_2024_operador,
                m.taxa_alfabetizacao-m.meta_alfabetizacao_2024 AS saldo_meta_pp,
                CASE WHEN m.meta_alfabetizacao_2024 IS NULL THEN 'Meta 2024 ausente'
                WHEN m.taxa_alfabetizacao IS NULL THEN 'Resultado publicado ausente'
                WHEN (p.operador='>' AND m.taxa_alfabetizacao>m.meta_alfabetizacao_2024)
                  OR (p.operador='>=' AND m.taxa_alfabetizacao>=m.meta_alfabetizacao_2024) THEN 'Atingiu'
                ELSE 'Não atingiu' END AS situacao,'OFICIAL' AS origem
                FROM meta_alfabetizacao_{table} m JOIN referencia_publicacao p
                  ON p.nivel={literal(level)} AND p.territorio={territory} AND p.ano_meta=2024
                WHERE m.ano=2024""")

        # UF também é utilizada analiticamente; a publicação de metas segue canônica.
        con.execute("""CREATE TABLE uf_agregado_2024 AS
            SELECT sigla_uf, taxa_alfabetizacao AS resultado_agregado
            FROM uf WHERE ano=2024 AND serie='2' AND rede='5'""")
        con.execute("""CREATE TABLE comparacao_uf_com_agregado AS
            SELECT c.*,u.resultado_agregado,
              u.resultado_agregado IS NOT NULL AS tem_resultado_agregado
            FROM comparacao_uf_2024 c LEFT JOIN uf_agregado_2024 u ON c.territorio=u.sigla_uf""")
        check("cardinalidade_uf", abs(con.execute("SELECT count(*) FROM comparacao_uf_com_agregado").fetchone()[0] - con.execute("SELECT count(*) FROM comparacao_uf_2024").fetchone()[0]))
        audit["uf_join"] = dict(zip(("linhas", "com_resultado_agregado"), con.execute("SELECT count(*),count(resultado_agregado) FROM comparacao_uf_com_agregado").fetchone()))
        check("uf_agregado_cobertura_incompleta", con.execute("SELECT count(*) FROM comparacao_uf_com_agregado WHERE NOT tem_resultado_agregado").fetchone()[0], "WARN")
        con.execute("DROP TABLE comparacao_uf_2024; ALTER TABLE comparacao_uf_com_agregado RENAME TO comparacao_uf_2024")

        con.execute("""CREATE TABLE conferencia_alunos AS WITH calculo AS (
            SELECT ano,id_municipio,count(*) AS elegiveis,sum(peso_aluno) AS soma_pesos,
              sum(CASE WHEN alfabetizado='1' THEN peso_aluno ELSE 0 END) AS pesos_alfabetizados,
              100.0*sum(CASE WHEN alfabetizado='1' THEN peso_aluno ELSE 0 END)/sum(peso_aluno) AS taxa_recalculada
            FROM alunos WHERE serie='2' AND rede='3' AND presenca='1' AND preenchimento_caderno='1'
              AND alfabetizado IN ('0','1') AND peso_aluno>0 AND isfinite(peso_aluno) AND isfinite(proficiencia)
            GROUP BY ano,id_municipio)
            SELECT coalesce(c.ano,r.ano) AS ano,coalesce(c.id_municipio,r.id_municipio) AS id_municipio,
              c.elegiveis,c.soma_pesos,c.pesos_alfabetizados,c.taxa_recalculada,
              r.taxa_alfabetizacao AS taxa_agregado,c.taxa_recalculada-r.taxa_alfabetizacao AS diferenca_pp,
              CASE WHEN c.taxa_recalculada IS NULL OR r.taxa_alfabetizacao IS NULL THEN 'NAO_AVALIAVEL'
                   ELSE 'CALCULADO_NAO_HOMOLOGADO' END AS status_conferencia
            FROM calculo c FULL OUTER JOIN (SELECT * FROM municipio WHERE serie='2' AND rede='3') r USING(ano,id_municipio)""")
        check("recalculo_diferenca_maior_001_pp_descritivo", con.execute("SELECT count(*) FROM conferencia_alunos WHERE abs(diferenca_pp)>0.01").fetchone()[0], "WARN")
        check("recalculo_cobertura_incompleta", con.execute("SELECT count(*) FROM conferencia_alunos WHERE status_conferencia='NAO_AVALIAVEL'").fetchone()[0], "WARN")

        # Autoridade da publicação selecionada, conferida contra os originais preservados.
        for name, level, territory, rate in (("comparacao_municipal_2024", "MUNICIPIO", "id_municipio", "resultado_publicado"), ("comparacao_uf_2024", "UF", "territorio", "resultado_publicado"), ("comparacao_brasil_2024", "BRASIL", "territorio", "resultado_publicado")):
            check(f"publicacao_original_{level}", con.execute(f"""SELECT count(*) FROM {name} c JOIN referencia_publicacao p
                ON p.nivel={literal(level)} AND p.territorio=c.{territory} AND p.ano_meta=2024
                WHERE (c.meta_alfabetizacao_2024 IS NULL) <> (p.meta_numerica IS NULL)
                   OR abs(c.meta_alfabetizacao_2024-p.meta_numerica)>0.000001
                   OR (c.{rate} IS NULL) <> (p.resultado_original IS NULL)
                   OR abs(c.{rate}-round(p.resultado_original,2))>0.000001""").fetchone()[0])
        if inject_failure:
            check("falha_proposital_demonstracao", 1)

        silver = ROOT / "data" / "silver" / run_id
        gold = ROOT / "data" / "gold" / run_id
        silver.mkdir(parents=True, exist_ok=False)
        gold.mkdir(parents=True, exist_ok=False)
        for table in (*TABLES, "territorio", "metas_anuais", "referencia_publicacao"):
            con.execute(f"COPY {ident(table)} TO {literal(silver / (table + '.parquet'))} (FORMAT PARQUET, COMPRESSION ZSTD)")
            audit["counts"][table] = con.execute(f"SELECT count(*) FROM {ident(table)}").fetchone()[0]
        outputs = ("comparacao_municipal_2024", "comparacao_uf_2024", "comparacao_brasil_2024", "conferencia_alunos")
        for table in outputs:
            con.execute(f"COPY {ident(table)} TO {literal(gold / (table + '.parquet'))} (FORMAT PARQUET, COMPRESSION ZSTD)")
            con.execute(f"COPY {ident(table)} TO {literal(gold / (table + '.csv'))} (HEADER, DELIMITER ',')")
            audit["counts"][table] = con.execute(f"SELECT count(*) FROM {ident(table)}").fetchone()[0]
        audit["municipal_status"] = dict(con.execute("SELECT situacao,count(*) FROM comparacao_municipal_2024 GROUP BY situacao").fetchall())
        audit.update(status="SUCCESS_WITH_WARNINGS" if any(c["status"] == "WARNING" for c in audit["checks"]) else "SUCCESS",
                     finished_at=now(), duration_seconds=round(time.monotonic() - started, 3), silver=str(silver), gold=str(gold))
        write_json(audit_path, audit)
        write_json(ROOT / "data" / "latest.json", {"run_id": run_id, "bronze": str(bronze), "silver": str(silver), "gold": str(gold), "audit": str(audit_path)})
        print(json.dumps({"status": audit["status"], "gold": str(gold), "municipal_status": audit["municipal_status"]}, ensure_ascii=False), flush=True)
    except Exception as exc:
        audit.update(status="FAILED", finished_at=now(), error=f"{type(exc).__name__}: {exc}", duration_seconds=round(time.monotonic() - started, 3))
        write_json(audit_path, audit)
        raise
    finally:
        con.close()
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bronze", type=Path, help="Reprocessar snapshot já baixado, sem nova leitura de nuvem")
    parser.add_argument("--inject-failure", action="store_true", help="Demonstrar bloqueio sem alterar a última versão publicada")
    args = parser.parse_args()
    from alerts import run_monitored
    run_monitored("batch_local", lambda: run(args.bronze, args.inject_failure))
