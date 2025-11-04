import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from haversine import haversine
from datetime import timedelta
import os
import sys


# ---------------------------
# Salvar Logs
# ---------------------------

LOG_FILE = "saida_python.log"
sys.stdout = open(LOG_FILE, "w", encoding="utf-8")

#------

def atualizar_matriz_distancia(
    arquivo_matriz,
    coords_antigos, datas_antigas,
    coords_novos, datas_novas,
    peso_tempo=1/30
):
    """
    Atualiza ou cria uma matriz de distâncias híbridas (geo + tempo)
    e salva em disco para reutilização futura.
    """

    # Verifica se já existe uma matriz salva
    if os.path.exists(f"./matrizes/{arquivo_matriz}"):
        dist_matrix = np.load(f"./matrizes/{arquivo_matriz}")
        n_antigo = dist_matrix.shape[0]
        print(f"[INFO] Matriz existente carregada ({n_antigo} pontos anteriores).")
    else:
        dist_matrix = np.zeros((0, 0))
        n_antigo = 0
        print("[INFO] Nenhuma matriz anterior encontrada. Criando nova.")

    # Dados combinados
    coords_total = coords_antigos + coords_novos
    datas_total = datas_antigas + datas_novas

    n_novo = len(coords_novos)
    n_total = n_antigo + n_novo

    # Cria nova matriz expandida
    nova_matrix = np.zeros((n_total, n_total))
    if n_antigo > 0:
        nova_matrix[:n_antigo, :n_antigo] = dist_matrix

    # Calcula apenas as distâncias novas
    for i in range(n_antigo, n_total):
        for j in range(i):
            dist_geo = haversine(coords_total[i], coords_total[j])
            dist_tempo = abs((datas_total[i] - datas_total[j]).days)
            dist_total = dist_geo + dist_tempo * peso_tempo * 5
            nova_matrix[i, j] = nova_matrix[j, i] = dist_total

    # Salva novamente
    np.save(f"python_scripts\matrizes\{arquivo_matriz}", nova_matrix)
    print(f"[INFO] Matriz atualizada salva com {n_total} pontos totais.")

    return nova_matrix


def detectar_clusters(df, eps_km=0.8, min_samples=2):
    resultados = []
    proximo_cluster_id = 0
    for doenca, grupo in df.groupby("diagnostico"):
        if grupo.empty:
            continue
        coords = list(zip(grupo["local_lat"], grupo["local_lon"]))
        datas = list(grupo["data"])
        dist_matrix = atualizar_matriz_distancia(
            f"{doenca}_{"arquivo_matriz"}",
            coords_antigos=[],
            datas_antigas=[],
            coords_novos=coords,
            datas_novas=datas
        )
        db = DBSCAN(eps=eps_km, min_samples=min_samples, metric="precomputed")
        labels = db.fit_predict(dist_matrix)
        labels_ajustados = np.where(labels != -1, labels + proximo_cluster_id, -1)
        grupo = grupo.copy()
        grupo["cluster"] = labels_ajustados
        resultados.append(grupo)
        max_label = labels[labels != -1].max() if np.any(labels != -1) else -1
        proximo_cluster_id += max_label + 1

    if resultados:
        return pd.concat(resultados, ignore_index=True)
    else:
        return pd.DataFrame(columns=df.columns.tolist() + ["cluster"])


def detectar_surtos_por_data(df, data_ref, janela_dias=30):
    data_ref = pd.to_datetime(data_ref)
    mask = (df['data'] >= data_ref - timedelta(days=janela_dias)) & \
           (df['data'] <= data_ref + timedelta(days=janela_dias))
    subset = df[mask].copy()
    if subset.empty:
        print(f"Nenhum dado encontrado no intervalo de ±{janela_dias} dias de {data_ref.date()}")
        return subset
    df_resultado = detectar_clusters(subset)
    return df_resultado