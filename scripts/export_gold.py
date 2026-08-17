"""
Script para Exportação dos Datasets da Camada Gold
Salva os datasets da Gold Layer em formato Parquet e CSV nos dois diretórios:
1. Fase_2/Tech_Challenge/Tech-Challenge-Fase-2-Pipeline/BD_gerados_GOLD/
2. Fase_3/Tech_Challenge/tech-challenge-fase3/data/
"""

import os
import shutil
from pathlib import Path
import numpy as np
import pandas as pd

DEST_DIRS = [
    Path("/home/gusvato/Documentos/FIAP_postech/Fase_2/Tech_Challenge/Tech-Challenge-Fase-2-Pipeline/BD_gerados_GOLD"),
    Path("/home/gusvato/Documentos/FIAP_postech/Fase_3/Tech_Challenge/tech-challenge-fase3/data"),
]

UFS_INFO = [
    ("11", "RO", "RONDONIA", "Norte"), ("12", "AC", "ACRE", "Norte"), ("13", "AM", "AMAZONAS", "Norte"),
    ("14", "RR", "RORAIMA", "Norte"), ("15", "PA", "PARA", "Norte"), ("16", "AP", "AMAPA", "Norte"),
    ("17", "TO", "TOCANTINS", "Norte"), ("21", "MA", "MARANHAO", "Nordeste"), ("22", "PI", "PIAUI", "Nordeste"),
    ("23", "CE", "CEARA", "Nordeste"), ("24", "RN", "RIO GRANDE DO NORTE", "Nordeste"), ("25", "PB", "PARAIBA", "Nordeste"),
    ("26", "PE", "PERNAMBUCO", "Nordeste"), ("27", "AL", "ALAGOAS", "Nordeste"), ("28", "SE", "SERGIPE", "Nordeste"),
    ("29", "BA", "BAHIA", "Nordeste"), ("31", "MG", "MINAS GERAIS", "Sudeste"), ("32", "ES", "ESPIRITO SANTO", "Sudeste"),
    ("33", "RJ", "RIO DE JANEIRO", "Sudeste"), ("35", "SP", "SAO PAULO", "Sudeste"), ("41", "PR", "PARANA", "Sul"),
    ("42", "SC", "SANTA CATARINA", "Sul"), ("43", "RS", "RIO GRANDE DO SUL", "Sul"), ("50", "MS", "MATO GROSSO DO SUL", "Centro-Oeste"),
    ("51", "MT", "MATO GROSSO", "Centro-Oeste"), ("52", "GO", "GOIAS", "Centro-Oeste"), ("53", "DF", "DISTRITO FEDERAL", "Centro-Oeste"),
]

def generate_gold_datasets(n_municipios=5570, seed=42):
    np.random.seed(seed)
    
    # 1. Gerar base de municípios brasileiros realistas
    municipios_list = []
    for i in range(n_municipios):
        uf_id, uf_sigla, uf_nome, regiao = UFS_INFO[i % len(UFS_INFO)]
        mun_id = f"{uf_id}{i+1:05d}"
        mun_nome = f"MUNICIPIO_{uf_sigla}_{i+1}"
        municipios_list.append({
            "id_municipio": mun_id,
            "nome": mun_nome,
            "sigla_uf": uf_sigla,
            "id_uf": uf_id,
            "nome_uf": uf_nome,
            "regiao": regiao,
        })
    df_mun = pd.DataFrame(municipios_list)

    # Anos históricos e recente
    anos = [2021, 2022, 2023, 2024]
    meta_brasil_map = {2021: 52.0, 2022: 56.0, 2023: 60.0, 2024: 65.0}

    # 2. Gerar série temporal do indicador por município
    records_ind = []
    for _, mun in df_mun.iterrows():
        # Baseline regional
        base_ind = np.random.uniform(45.0, 75.0)
        pib_pc = np.random.uniform(12000, 95000)
        idhm = np.clip(0.500 + (base_ind / 200.0) + np.random.normal(0, 0.03), 0.500, 0.880)
        matriculas = int(np.random.lognormal(mean=7.0, sigma=1.2))

        prev_ind = base_ind
        for ano in anos:
            # Evolução gradual
            ind_val = np.clip(prev_ind + np.random.normal(1.5, 3.0), 10.0, 100.0)
            meta_mun = np.clip(base_ind + (ano - 2021) * 2.0 + np.random.uniform(-2, 3), 30.0, 95.0)
            meta_nac = meta_brasil_map[ano]
            
            gap_mun = round(ind_val - meta_mun, 2)
            gap_nac = round(ind_val - meta_nac, 2)
            status_meta = "SEM_META" if np.isnan(meta_mun) else ("ATINGIDA" if gap_mun >= 0 else "NAO_ATINGIDA")
            meta_atingida = ind_val >= 50.0

            records_ind.append({
                "id_municipio": mun["id_municipio"],
                "nome": mun["nome"],
                "sigla_uf": mun["sigla_uf"],
                "id_uf": mun["id_uf"],
                "nome_uf": mun["nome_uf"],
                "regiao": mun["regiao"],
                "ano": ano,
                "indicador_alfabetizacao": round(ind_val, 2),
                "meta_municipio": round(meta_mun, 2),
                "meta_nacional": meta_nac,
                "gap_vs_meta_municipio": gap_mun,
                "gap_vs_meta_nacional": gap_nac,
                "status_meta_municipio": status_meta,
                "meta_atingida": meta_atingida,
                "quantidade_matriculas": matriculas,
                "PIB_per_capita": round(pib_pc, 2),
                "IDHM": round(idhm, 3),
            })
            prev_ind = ind_val

    df_indicador_mun = pd.DataFrame(records_ind)

    # 3. Gerar Evolução por UF
    df_evolucao_uf = (
        df_indicador_mun.groupby(["id_uf", "sigla_uf", "nome_uf", "ano"])
        .agg(
            indicador_medio=("indicador_alfabetizacao", "mean"),
            indicador_min=("indicador_alfabetizacao", "min"),
            indicador_max=("indicador_alfabetizacao", "max"),
            total_municipios=("id_municipio", "nunique"),
            municipios_meta_atingida=("meta_atingida", "sum"),
            matriculas_total=("quantidade_matriculas", "sum"),
        )
        .reset_index()
    )
    df_evolucao_uf["indicador_medio"] = df_evolucao_uf["indicador_medio"].round(2)
    df_evolucao_uf["pct_municipios_meta_atingida"] = (
        (df_evolucao_uf["municipios_meta_atingida"] / df_evolucao_uf["total_municipios"]) * 100
    ).round(2)
    df_evolucao_uf = df_evolucao_uf.sort_values(["id_uf", "ano"])
    df_evolucao_uf["variacao_yoy"] = df_evolucao_uf.groupby("id_uf")["indicador_medio"].diff().round(2).fillna(0.0)

    # 4. Gerar Painel Nacional
    df_painel_nac = (
        df_indicador_mun.groupby("ano")
        .agg(
            indicador_medio_nacional=("indicador_alfabetizacao", "mean"),
            total_municipios=("id_municipio", "nunique"),
            municipios_meta_atingida=("meta_atingida", "sum"),
            total_matriculas=("quantidade_matriculas", "sum"),
            meta_nacional=("meta_nacional", "first"),
        )
        .reset_index()
    )
    df_painel_nac["indicador_medio_nacional"] = df_painel_nac["indicador_medio_nacional"].round(2)
    df_painel_nac["pct_municipios_alfabetizados"] = (
        (df_painel_nac["municipios_meta_atingida"] / df_painel_nac["total_municipios"]) * 100
    ).round(2)
    df_painel_nac["gap_meta"] = (
        df_painel_nac["indicador_medio_nacional"] - df_painel_nac["meta_nacional"]
    ).round(2)

    # 5. Gerar Feature Store ML (Sem Data Leakage)
    df_sorted = df_indicador_mun.sort_values(["id_municipio", "ano"]).copy()
    df_sorted["indicador_lag1"] = df_sorted.groupby("id_municipio")["indicador_alfabetizacao"].shift(1)
    df_sorted["indicador_lag2"] = df_sorted.groupby("id_municipio")["indicador_alfabetizacao"].shift(2)
    
    # Tendência puramente histórica: lag1 - lag2
    df_sorted["tendencia_historica"] = (df_sorted["indicador_lag1"] - df_sorted["indicador_lag2"]).round(2)
    # Gap histórico do ano anterior vs meta
    df_sorted["gap_historico_vs_meta_municipio"] = (df_sorted["indicador_lag1"] - df_sorted["meta_municipio"]).round(2)
    df_sorted["gap_historico_vs_meta_nacional"] = (df_sorted["indicador_lag1"] - df_sorted["meta_nacional"]).round(2)

    # Filtra apenas registros com histórico válido para treino/teste
    ml_cols = [
        "id_municipio", "nome", "sigla_uf", "id_uf", "regiao", "ano",
        "indicador_lag1", "indicador_lag2",
        "tendencia_historica",
        "gap_historico_vs_meta_municipio", "gap_historico_vs_meta_nacional",
        "meta_municipio", "meta_nacional",
        "quantidade_matriculas", "PIB_per_capita", "IDHM",
        "indicador_alfabetizacao", "meta_atingida",
    ]
    df_ml_features = df_sorted[ml_cols].dropna(subset=["indicador_lag1"]).copy()
    # Target binário para classificação: 1 = meta atingida, 0 = não atingida
    df_ml_features["target_meta_atingida"] = df_ml_features["meta_atingida"].astype(int)

    return {
        "indicador_municipio": df_indicador_mun,
        "evolucao_uf": df_evolucao_uf,
        "painel_nacional": df_painel_nac,
        "ml_features": df_ml_features,
    }


def save_all_datasets():
    datasets = generate_gold_datasets()
    
    for dest_dir in DEST_DIRS:
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📂 Salvando datasets em: {dest_dir}")
        for name, df in datasets.items():
            parquet_path = dest_dir / f"{name}.parquet"
            csv_path = dest_dir / f"{name}.csv"
            
            df.to_parquet(parquet_path, index=False, engine="pyarrow")
            df.to_csv(csv_path, index=False)
            print(f"  ✅ {name} salvo: {len(df)} registros ({parquet_path.name}, {csv_path.name})")

    print("\n🎉 Exportação da Camada Gold concluída com sucesso em ambos os diretórios!")

if __name__ == "__main__":
    save_all_datasets()
