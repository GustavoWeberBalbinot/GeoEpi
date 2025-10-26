import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from haversine import haversine
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import folium
import os

# ---------------------------
# Caminhos
# ---------------------------
base_path = os.path.dirname(__file__)
imagens_path = os.path.join(base_path, "imagens")
csv_path = os.path.join(base_path, "dados_pacientes.csv")

os.makedirs(imagens_path, exist_ok=True)

# ---------------------------
# Ler CSV
# ---------------------------
df = pd.read_csv(csv_path)
df["data"] = pd.to_datetime(df["data"], errors="coerce")
df = df.dropna(subset=["data", "local_lat", "local_lon"])  # remove linhas inválidas

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
# Função: gráficos
# ---------------------------
def gerar_graficos(df_resultado, subset=None, tipo="geral", data_ref=None, janela_dias=30):
    cores_doencas = {
        'Dengue': 'orange',
        'COVID': 'red',
        'Influenza': 'blue',
        'Zika': 'green'
    }

    if tipo == "geral":
        df_plot = df_resultado
        # Gráfico de clusters
        plt.figure(figsize=(8,6))
        for doenca, grupo in df_plot.groupby('diagnostico'):
            cor = cores_doencas.get(doenca, 'gray')
            grupo_cluster = grupo[grupo['cluster'] != -1]
            grupo_ruido = grupo[grupo['cluster'] == -1]

            plt.scatter(grupo_cluster['local_lon'], grupo_cluster['local_lat'],
                        c=cor, label=f"{doenca} (cluster)", alpha=0.7, s=70, edgecolor='black', marker='o')
            plt.scatter(grupo_ruido['local_lon'], grupo_ruido['local_lat'],
                        c=cor, label=f"{doenca} (isolado)", alpha=0.5, s=70, edgecolor='black', marker='x')

        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Clusters gerais por doença')
        plt.legend(title='Legenda', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(imagens_path, "cluster_geral.png"), bbox_inches='tight')
        plt.close()

        # Gráfico de barras
        contagem_doencas = df_plot['diagnostico'].value_counts()
        plt.figure(figsize=(8,6))
        contagem_doencas.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.xlabel('Diagnóstico')
        plt.ylabel('Quantidade de casos')
        plt.title('Quantidade total de casos por diagnóstico')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(imagens_path, "barras_geral.png"))
        plt.close()

    elif tipo == "data" and subset is not None:
        df_plot = subset
        plt.figure(figsize=(8,6))
        for doenca, grupo in df_plot.groupby('diagnostico'):
            cor = cores_doencas.get(doenca, 'gray')
            grupo_cluster = grupo[grupo['cluster'] != -1]
            grupo_ruido = grupo[grupo['cluster'] == -1]

            plt.scatter(grupo_cluster['local_lon'], grupo_cluster['local_lat'],
                        c=cor, label=f"{doenca} (cluster)", alpha=0.7, s=70, edgecolor='black', marker='o')
            plt.scatter(grupo_ruido['local_lon'], grupo_ruido['local_lat'],
                        c=cor, label=f"{doenca} (isolado)", alpha=0.5, s=70, edgecolor='black', marker='x')

        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title(f'Clusters detectados ±{janela_dias} dias de {data_ref.date()}')
        plt.legend(title='Legenda', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(imagens_path, "cluster_data.png"), bbox_inches='tight')
        plt.close()

        contagem_doencas = df_plot['diagnostico'].value_counts()
        plt.figure(figsize=(8,6))
        contagem_doencas.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.xlabel('Diagnóstico')
        plt.ylabel('Quantidade de casos')
        plt.title(f'Casos entre {data_ref.date()} ± {janela_dias} dias')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(imagens_path, "barras_data.png"))
        plt.close()

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

def gerar_mapa_clusters(df, arquivo_saida="mapa_clusters.html"):
    """
    Gera mapa interativo com clusters.
    """
    # Pega coordenadas médias para centralizar o mapa
    lat_media = df['local_lat'].mean()
    lon_media = df['local_lon'].mean()
    mapa = folium.Map(location=[lat_media, lon_media], zoom_start=12)
    
    # Cores para clusters (clusters -1 = ruído)
    cores = ["red", "blue", "green", "orange", "purple", "pink", "brown", "gray"]
    
    for _, row in df.iterrows():
        cluster_id = row["cluster"]
        cor = "lightgray" if cluster_id == -1 else cores[cluster_id % len(cores)]
        
        folium.Circle(
            location=[row['local_lat'], row['local_lon']],
            radius=200,  # tamanho do círculo em metros
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=0.4,  # transparência
            popup=f"{row['diagnostico']} (Cluster {cluster_id})"
        ).add_to(mapa)
    
    # Salvar HTML
    mapa.save(arquivo_saida)
    print(f"Mapa interativo salvo em {arquivo_saida}")

# ---------------------------
# Execução principal
# ---------------------------
if __name__ == "__main__":
    # 1️⃣ Clusters gerais
    df_geral = detectar_clusters(df)
    print("Clusters detectados (geral):")
    print(df_geral[["diagnostico", "data", "local_lat", "local_lon", "cluster"]]
          .to_string(index=False))  # índice removido

    # 2️⃣ Gráficos gerais
    gerar_graficos(df_geral, tipo="geral")

    # 3️⃣ Clusters e gráficos por data
    data_exemplo = "2025-10-10"
    df_data = detectar_surtos_por_data(df, data_exemplo)
    if not df_data.empty:
        print(f"\nSurtos detectados em torno de {data_exemplo}:")
        print(df_data[["cluster", "diagnostico", "data", "local_lat", "local_lon"]]
              .to_string(index=False))  # índice removido
        gerar_graficos(df_data, subset=df_data, tipo="data", data_ref=pd.to_datetime(data_exemplo))
    print(f"\nGráficos salvos em: {imagens_path}")

    # Gerar mapa interativo
    gerar_mapa_clusters(df_geral, arquivo_saida="mapa_clusters.html")
