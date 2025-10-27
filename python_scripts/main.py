from gerar_imagens import gerar_graficos, gerar_mapa_clusters, gerar_mapa_clusters_validos
from dbscan import detectar_clusters, detectar_surtos_por_data
from coleta_dados_google import baixar_csv
import os
import pandas as pd
import sys
import datetime


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

if __name__ == "__main__":
    # 1️⃣ Clusters gerais
    df_geral = detectar_clusters(df)
    print("Clusters detectados (geral):")
    print(df_geral[["diagnostico", "data", "local_lat", "local_lon", "cluster"]]
          .to_string(index=False))  # índice removido

    # 2️⃣ Gráficos gerais
    gerar_graficos(df_geral, tipo="geral")

    # 3️⃣ Clusters e gráficos por data
    if len(sys.argv) > 1:
        data_ref = sys.argv[1]
        print(f"Rodando DBSCAN para a data: {data_ref}")
    else:
        data_ref = '2025-10-10'
    df_data = detectar_surtos_por_data(df, data_ref)
    if not df_data.empty:
        print(f"\nSurtos detectados em torno de {data_ref}:")
        print(df_data[["cluster", "diagnostico", "data", "local_lat", "local_lon"]]
              .to_string(index=False))  # índice removido
        gerar_graficos(df_data, subset=df_data, tipo="data", data_ref=pd.to_datetime(data_ref))
    print(f"\nGráficos salvos em: {imagens_path}")

    # Gerar mapa interativo
    gerar_mapa_clusters(df_geral, arquivo_saida="mapa_clusters.html")
    gerar_mapa_clusters_validos(df_geral, arquivo_saida="mapa_clusters_validos.html")
