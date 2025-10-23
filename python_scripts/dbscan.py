import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from haversine import haversine
from datetime import datetime, timedelta
import os

# Caminho do arquivo CSV (mesma pasta do script)
base_path = os.path.dirname(__file__)
csv_path = os.path.join(base_path, "dados_pacientes.csv")

# Ler o CSV
df = pd.read_csv(csv_path)
df['data'] = pd.to_datetime(df['data'])

# Converter a coluna de data
df["data"] = pd.to_datetime(df["data"], errors="coerce")

# Função: matriz de distância (espaço + tempo)
def distancia_hibrida(coords, datas, peso_tempo=1/30):
    """
    Calcula uma matriz de distâncias combinando:
    - Distância geográfica (km)
    - Diferença de tempo (dias * peso_tempo)
    peso_tempo = quanto 1 dia "vale" em km
    """
    n = len(coords)
    dist_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            dist_geo = haversine(coords[i], coords[j])  # km
            dist_tempo = abs((datas[i] - datas[j]).days)  # dias
            # Combina tempo e espaço (30 dias ≈ 5 km extras)
            dist_total = dist_geo + dist_tempo * peso_tempo * 5
            dist_matrix[i, j] = dist_matrix[j, i] = dist_total
    return dist_matrix

def detectar_surtos_em_data(df, data_ref, raio_km=5, janela_dias=30, eps_min=2):
    """
    Detecta surtos próximos de uma data específica.
    """
    # Converter data_ref para datetime
    data_ref = pd.to_datetime(data_ref)
    
    # Filtrar os dados dentro da janela de tempo desejada
    mask = (df['data'] >= data_ref - timedelta(days=janela_dias)) & \
           (df['data'] <= data_ref + timedelta(days=janela_dias))
    subset = df[mask].copy()
    
    # Converter coordenadas para radianos (para usar DBSCAN com haversine)
    coords = np.radians(subset[['local_lat', 'local_lon']])
    
    # Distância máxima (em km → radianos)
    eps = raio_km / 6371.0
    
    # Rodar DBSCAN espacial
    db = DBSCAN(eps=eps, min_samples=eps_min, metric='haversine').fit(coords)
    subset['cluster'] = db.labels_
    
    # Agrupar e mostrar surtos
    surtos = subset[subset['cluster'] != -1].groupby(['cluster', 'diagnostico']).agg({
        'data': ['min', 'max', 'count'],
        'local_lat': 'mean',
        'local_lon': 'mean'
    }).reset_index()
    
    surtos.columns = ['cluster', 'diagnostico', 'data_inicial', 'data_final', 'casos', 'lat_media', 'lon_media']
    return surtos

# Parâmetros do DBSCAN
EPS = 5          # raio máximo (5 km)
MIN_SAMPLES = 2  # mínimo de casos para formar cluster

resultados = []

# Agrupar por tipo de doença
for doenca, grupo in df.groupby("diagnostico"):
    coords = list(zip(grupo["local_lat"], grupo["local_lon"]))
    datas = list(grupo["data"])
    
    dist_matrix = distancia_hibrida(coords, datas)
    
    db = DBSCAN(eps=EPS, min_samples=MIN_SAMPLES, metric="precomputed")
    labels = db.fit_predict(dist_matrix)
    
    grupo = grupo.copy()
    grupo["cluster"] = labels
    resultados.append(grupo)

# Combina tudo
df_resultado = pd.concat(resultados)

# Exibir resultado
print("\nClusters detectados:")
print(df_resultado[["diagnostico", "data", "local_lat", "local_lon", "cluster"]])



#Exibir resultado por em torno do Período
surtos = detectar_surtos_em_data(df, '2025-10-10')
print(surtos)
