"""Métricas de correspondência e cardinalidade, com exceções identificadas por chave."""
def join_profile(con, name, left_sql, right_sql, keys, allowed_missing=()):
    columns = ",".join('"' + key.replace('"', '""') + '"' for key in keys)

    def grouped(sql):
        return {tuple(row[:-1]): row[-1] for row in con.execute(
            f"SELECT {columns},count(*) FROM ({sql}) GROUP BY {columns}").fetchall()}

    left, right = grouped(left_sql), grouped(right_sql)
    allowed = set(map(tuple, allowed_missing))
    valid_right = {key: count for key, count in right.items() if all(v is not None for v in key)}
    missing = set(left) - set(valid_right)
    total = sum(left.values())
    matched = sum(count for key, count in left.items() if key in valid_right)
    allowed_rows = sum(count for key, count in left.items() if key in allowed)
    output_rows = sum(count * max(valid_right.get(key, 0), 1) for key, count in left.items())
    violations = (len(missing - allowed) + sum(count-1 for count in right.values() if count>1)
                  + sum(count for key,count in left.items() if None in key)
                  + sum(count for key,count in right.items() if None in key))
    return {"name": name, "keys": keys, "input_rows": total, "matched_rows": matched,
            "unmatched_rows": total-matched, "output_rows_left_join": output_rows,
            "match_rate": matched/total if total else None,
            "minimum_match_rate": (total-allowed_rows)/total if total else None,
            "allowed_missing_key_count": len(allowed), "missing_key_count": len(missing),
            "unexpected_missing_keys": [list(key) for key in sorted(missing-allowed, key=str)],
            "blocking_violations": violations}
