import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from haversine import haversine
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

# Caminho do arquivo CSV (mesma pasta do script)
base_path = os.path.dirname(__file__)
imagens_path = os.path.join(base_path, "imagens")
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
periodo = '2025-10-10'
surtos = detectar_surtos_em_data(df, periodo)
print(surtos)


#Gerar Gráficos:
# Configura cores diferentes para cada cluster
cores = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

plt.figure(figsize=(8,6))
for cluster_id in df_resultado['cluster'].unique():
    grupo = df_resultado[df_resultado['cluster'] == cluster_id]
    cor = 'black' if cluster_id == -1 else cores[cluster_id % len(cores)]
    plt.scatter(grupo['local_lon'], grupo['local_lat'], c=cor, label=f'Cluster {cluster_id}', alpha=0.6)

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Clusters detectados')
plt.legend()
plt.tight_layout()

# Salva a figura como cluster.png na mesma pasta
fig_path = os.path.join(imagens_path, "cluster.png")
plt.savefig(fig_path)
plt.close()  # fecha a figura para liberar memória

#Gráfico de Barras

# Agrupa por diagnóstico e conta casos
contagem_doencas = df['diagnostico'].value_counts()  # Series: índice=diagnóstico, valor=quantidade

# Cria gráfico de barras
plt.figure(figsize=(8,6))
contagem_doencas.plot(kind='bar', color='skyblue', edgecolor='black')
plt.xlabel('Diagnóstico')
plt.ylabel('Quantidade de casos')
plt.title(f'Quantidade de casos em {periodo} ± 30 dias de diferença')
plt.xticks(rotation=45)
plt.tight_layout()

# Salva a figura
fig_path = os.path.join(imagens_path, "barras_doencas.png")
plt.savefig(fig_path)
plt.close()