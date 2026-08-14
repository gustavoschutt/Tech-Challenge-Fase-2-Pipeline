import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from google.cloud import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("silver.transform")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tc-alfabetizacao")
BUCKET_NAME = os.getenv("GCS_BUCKET", "tc-alfabetizacao-datalake")
RUN_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

BRONZE_PREFIX = "bronze"
SILVER_PREFIX = "silver"


# ---------------------------------------------------------------------------
# Leitura da camada Bronze
# ---------------------------------------------------------------------------

def read_bronze(gcs_client: storage.Client, entity: str) -> pd.DataFrame:
    """Lê o arquivo Parquet mais recente da camada Bronze."""
    bucket = gcs_client.bucket(BUCKET_NAME)
    prefix = f"{BRONZE_PREFIX}/{entity}/ingestion_date={RUN_DATE}/"
    blobs = list(bucket.list_blobs(prefix=prefix))
    if not blobs:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em: {prefix}")
    blob = blobs[0]
    local_path = Path(f"/tmp/bronze_{entity}.parquet")
    blob.download_to_filename(str(local_path))
    df = pd.read_parquet(local_path)
    logger.info(f"[{entity}] Bronze carregado: {len(df)} registros")
    return df


def read_bronze_streaming(gcs_client: storage.Client, date_str: str = RUN_DATE) -> pd.DataFrame:
    """Lê eventos de streaming da camada Bronze (JSON) para micro-batch."""
    bucket = gcs_client.bucket(BUCKET_NAME)
    prefix = f"{BRONZE_PREFIX}/streaming/date={date_str}/"
    blobs = list(bucket.list_blobs(prefix=prefix))
    if not blobs:
        blobs = list(bucket.list_blobs(prefix=f"{BRONZE_PREFIX}/streaming/"))
    if not blobs:
        logger.info("Nenhum evento de streaming encontrado na camada Bronze.")
        return pd.DataFrame()

    records = []
    for blob in blobs:
        try:
            content = blob.download_as_text()
            for line in content.strip().split("\n"):
                if not line.strip():
                    continue
                evt = json.loads(line)
                payload = evt.get("payload", {})
                rec = {
                    "event_id": evt.get("event_id"),
                    "event_type": evt.get("event_type"),
                    "event_timestamp": evt.get("timestamp"),
                    "id_municipio": str(payload.get("id_municipio", "")),
                    "ano": int(payload.get("ano", 2024)),
                    "indicador_alfabetizacao": float(payload.get("indicador_alfabetizacao")) if payload.get("indicador_alfabetizacao") is not None else None,
                    "quantidade_matriculas": payload.get("quantidade_matriculas"),
                    "_source": "streaming_pubsub",
                }
                records.append(rec)
        except Exception as e:
            logger.warning(f"Erro ao parsear blob de streaming {blob.name}: {e}")

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    logger.info(f"Bronze Streaming carregado: {len(df)} eventos")
    return df


def integrate_streaming_into_indicador(
    indicador_df: pd.DataFrame, streaming_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Integra eventos de streaming aos dados batch do indicador.
    Atualizações de streaming sobrescrevem medições antigas para o mesmo (id_municipio, ano).
    """
    if streaming_df is None or streaming_df.empty:
        return indicador_df

    logger.info(f"Integrando {len(streaming_df)} eventos de streaming ao Indicador...")
    valid_stream = streaming_df[streaming_df["id_municipio"].str.len() > 0].copy()
    if valid_stream.empty:
        return indicador_df

    cols_to_keep = [c for c in ["id_municipio", "ano", "indicador_alfabetizacao", "quantidade_matriculas"] if c in indicador_df.columns]
    stream_subset = valid_stream[[c for c in cols_to_keep if c in valid_stream.columns]].copy()

    combined = pd.concat([indicador_df, stream_subset], ignore_index=True)
    combined = combined.drop_duplicates(subset=["id_municipio", "ano"], keep="last")
    return combined


# ---------------------------------------------------------------------------
# Transformações comuns
# ---------------------------------------------------------------------------

def remove_duplicates(df: pd.DataFrame, subset: list) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset).copy()
    removed = before - len(df)
    if removed:
        logger.warning(f"Duplicatas removidas: {removed}")
    return df


def fill_missing(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    """rules: {coluna: valor_padrão}"""
    df = df.copy()
    for col, default in rules.items():
        if col in df.columns and default is not None:
            nulls = df[col].isna().sum()
            if nulls:
                logger.warning(f"Coluna '{col}': {nulls} valores nulos → preenchido com '{default}'")
            df[col] = df[col].fillna(default)
    return df


def normalize_text_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.upper()
                .str.normalize("NFKD")
                .str.encode("ascii", errors="ignore")
                .str.decode("ascii")
            )
    return df


def cast_types(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """schema: {coluna: dtype}"""
    df = df.copy()
    for col, dtype in schema.items():
        if col in df.columns:
            try:
                df[col] = df[col].astype(dtype)
            except Exception as e:
                logger.warning(f"Cast falhou para '{col}' → {dtype}: {e}")
    return df


def validate_referential_integrity(
    df: pd.DataFrame,
    ref_df: pd.DataFrame,
    key: str,
    ref_key: str,
    entity_name: str,
):
    """Verifica se todas as chaves existem na tabela de referência."""
    invalid = ~df[key].isin(ref_df[ref_key])
    count = invalid.sum()
    if count:
        logger.warning(
            f"[{entity_name}] {count} registros com '{key}' não encontrado na referência"
        )
    return df[~invalid].copy()


# ---------------------------------------------------------------------------
# Transformações específicas por entidade
# ---------------------------------------------------------------------------

def transform_ufs(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transformando UFs...")
    df = remove_duplicates(df, subset=["id_uf"])
    df = normalize_text_columns(df, ["sigla", "nome"])
    df = cast_types(df, {"id_uf": str})
    df["_silver_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df[["id_uf", "sigla", "nome", "_silver_timestamp"]]


def transform_municipios(df: pd.DataFrame, ufs_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transformando Municípios...")
    df = remove_duplicates(df, subset=["id_municipio"])
    df = normalize_text_columns(df, ["nome"])
    df = cast_types(df, {"id_municipio": str, "id_uf": str})
    df = fill_missing(df, {"nome": "NAO INFORMADO"})
    # Validação de integridade referencial
    df = validate_referential_integrity(df, ufs_df, "sigla_uf", "sigla", "municipios")
    df["_silver_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df[["id_municipio", "nome", "sigla_uf", "id_uf", "_silver_timestamp"]]


def transform_indicador(
    df: pd.DataFrame,
    municipios_df: pd.DataFrame,
    streaming_df: pd.DataFrame = None,
) -> pd.DataFrame:
    logger.info("Transformando Indicador de Alfabetização...")
    if streaming_df is not None and not streaming_df.empty:
        df = integrate_streaming_into_indicador(df, streaming_df)

    df = remove_duplicates(df, subset=["id_municipio", "ano"])
    df = cast_types(df, {
        "id_municipio": str,
        "ano": int,
        "indicador_alfabetizacao": float,
        "quantidade_matriculas": "Int64",
    })
    df = validate_referential_integrity(df, municipios_df, "id_municipio", "id_municipio", "indicador")
    # Criar flag de meta atingida (ponto de corte 743 → indicador >= 50% por convenção do dataset)
    if "indicador_alfabetizacao" in df.columns:
        df["meta_atingida"] = df["indicador_alfabetizacao"] >= 50.0
    df["_silver_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df


def transform_alunos(df: pd.DataFrame, municipios_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma microdados de alunos da avaliação de alfabetização (Saeb).
    Aplica o ponto de corte de 743 pontos na escala de proficiência Saeb.
    """
    logger.info("Transformando Alunos (Microdados SAEB)...")
    df = cast_types(df, {
        "ano": int,
        "id_municipio": str,
        "proficiencia": float,
    })
    if "id_aluno" in df.columns:
        df = remove_duplicates(df, subset=["id_aluno", "ano"])

    # Ponto de corte do Indicador Criança Alfabetizada: 743 pontos na escala Saeb
    if "proficiencia" in df.columns:
        df["aluno_alfabetizado"] = df["proficiencia"] >= 743.0

    if "id_municipio" in df.columns:
        df = validate_referential_integrity(df, municipios_df, "id_municipio", "id_municipio", "alunos")

    df["_silver_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df


def transform_meta_brasil(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transformando Meta Brasil...")
    df = remove_duplicates(df, subset=["ano"])
    df = cast_types(df, {"ano": int, "meta": float})
    df["_silver_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df


def transform_meta_uf(df: pd.DataFrame, ufs_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transformando Meta por UF...")
    df = remove_duplicates(df, subset=["id_uf", "ano"])
    df = cast_types(df, {"id_uf": str, "ano": int, "meta": float})
    df = validate_referential_integrity(df, ufs_df, "id_uf", "id_uf", "meta_uf")
    df["_silver_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df


def transform_meta_municipio(df: pd.DataFrame, municipios_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transformando Meta por Município...")
    df = remove_duplicates(df, subset=["id_municipio", "ano"])
    df = cast_types(df, {"id_municipio": str, "ano": int, "meta": float})
    df = validate_referential_integrity(df, municipios_df, "id_municipio", "id_municipio", "meta_municipio")
    df["_silver_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df


# ---------------------------------------------------------------------------
# Salvamento na camada Silver
# ---------------------------------------------------------------------------

def save_silver(
    df: pd.DataFrame,
    gcs_client: storage.Client,
    entity: str,
):
    bucket = gcs_client.bucket(BUCKET_NAME)
    blob_path = f"{SILVER_PREFIX}/{entity}/processed_date={RUN_DATE}/{entity}.parquet"
    local_path = Path(f"/tmp/silver_{entity}.parquet")
    df.to_parquet(local_path, index=False, engine="pyarrow")
    bucket.blob(blob_path).upload_from_filename(str(local_path))
    gcs_uri = f"gs://{BUCKET_NAME}/{blob_path}"
    logger.info(f"Silver salvo: {gcs_uri} ({len(df)} registros)")
    return gcs_uri


# ---------------------------------------------------------------------------
# Orquestração Silver
# ---------------------------------------------------------------------------

def run_silver_pipeline():
    logger.info("=== Iniciando Silver Pipeline ===")
    gcs_client = storage.Client(project=PROJECT_ID)
    errors = []

    try:
        ufs_raw = read_bronze(gcs_client, "ufs")
        ufs = transform_ufs(ufs_raw)
        save_silver(ufs, gcs_client, "ufs")
    except Exception as e:
        logger.error(f"UFs: {e}")
        errors.append("ufs")

    try:
        mun_raw = read_bronze(gcs_client, "municipios")
        municipios = transform_municipios(mun_raw, ufs)
        save_silver(municipios, gcs_client, "municipios")
    except Exception as e:
        logger.error(f"Municipios: {e}")
        errors.append("municipios")

    # Carrega streaming (micro-batch)
    streaming_df = None
    try:
        streaming_df = read_bronze_streaming(gcs_client)
        if not streaming_df.empty:
            save_silver(streaming_df, gcs_client, "streaming_events")
    except Exception as e:
        logger.warning(f"Streaming Bronze não carregado: {e}")

    try:
        ind_raw = read_bronze(gcs_client, "indicador_alfabetizacao")
        indicador = transform_indicador(ind_raw, municipios, streaming_df)
        save_silver(indicador, gcs_client, "indicador_alfabetizacao")
    except Exception as e:
        logger.error(f"Indicador: {e}")
        errors.append("indicador_alfabetizacao")

    try:
        alunos_raw = read_bronze(gcs_client, "alunos")
        alunos = transform_alunos(alunos_raw, municipios)
        save_silver(alunos, gcs_client, "alunos")
    except Exception as e:
        logger.error(f"Alunos: {e}")
        errors.append("alunos")

    try:
        mb_raw = read_bronze(gcs_client, "meta_brasil")
        meta_brasil = transform_meta_brasil(mb_raw)
        save_silver(meta_brasil, gcs_client, "meta_brasil")
    except Exception as e:
        logger.error(f"Meta Brasil: {e}")
        errors.append("meta_brasil")

    try:
        muf_raw = read_bronze(gcs_client, "meta_uf")
        meta_uf = transform_meta_uf(muf_raw, ufs)
        save_silver(meta_uf, gcs_client, "meta_uf")
    except Exception as e:
        logger.error(f"Meta UF: {e}")
        errors.append("meta_uf")

    try:
        mmun_raw = read_bronze(gcs_client, "meta_municipio")
        meta_municipio = transform_meta_municipio(mmun_raw, municipios)
        save_silver(meta_municipio, gcs_client, "meta_municipio")
    except Exception as e:
        logger.error(f"Meta Municipio: {e}")
        errors.append("meta_municipio")

    logger.info(f"=== Silver concluído. Erros: {errors} ===")
    return errors


if __name__ == "__main__":
    run_silver_pipeline()
