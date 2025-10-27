import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from haversine import haversine
from datetime import timedelta
import sys
from gerar_imagens import gerar_graficos, gerar_mapa_clusters


# ---------------------------
# Salvar Logs
# ---------------------------

LOG_FILE = "saida_python.log"
sys.stdout = open(LOG_FILE, "w", encoding="utf-8")  # redireciona prints para o arquivo


# ---------------------------
# Função de distância híbrida
# ---------------------------
def distancia_hibrida(coords, datas, peso_tempo=1/30):
    n = len(coords)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dist_geo = haversine(coords[i], coords[j])
            dist_tempo = abs((datas[i] - datas[j]).days)
            dist_total = dist_geo + dist_tempo * peso_tempo * 5
            dist_matrix[i, j] = dist_matrix[j, i] = dist_total
    return dist_matrix

# ---------------------------
# Função DBSCAN
# ---------------------------
def detectar_clusters(df, eps_km=5, min_samples=2):
    resultados = []
    for doenca, grupo in df.groupby("diagnostico"):
        if grupo.empty:
            continue
        coords = list(zip(grupo["local_lat"], grupo["local_lon"]))
        datas = list(grupo["data"])
        dist_matrix = distancia_hibrida(coords, datas)
        db = DBSCAN(eps=eps_km, min_samples=min_samples, metric="precomputed")
        labels = db.fit_predict(dist_matrix)
        grupo = grupo.copy()
        grupo["cluster"] = labels
        resultados.append(grupo)
    if resultados:
        return pd.concat(resultados)
    else:
        return pd.DataFrame(columns=df.columns.tolist() + ["cluster"])


# ---------------------------
# DBSCAN por data
# ---------------------------
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