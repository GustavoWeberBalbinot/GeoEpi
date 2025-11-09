from gerar_imagens import gerar_mapa_clusters, gerar_mapa_clusters_validos, gerar_grafico_geral, gerar_grafico_tempo, gerar_graficos_pizza
from dbscan import detectar_clusters, detectar_surtos_por_data
from coleta_dados_google import baixar_e_formatar_csv
import os
import pandas as pd
import sys
import time
from datetime import date


# Caminhos
base_path = os.path.dirname(__file__)
imagens_path = os.path.join(base_path, "imagens")
csv_path = os.path.join(base_path, "dados_pacientes.csv")
os.makedirs(imagens_path, exist_ok=True)



# Ler CSV
df = pd.read_csv(csv_path, sep=",", quotechar='"', engine="python")
df["data"] = pd.to_datetime(df["data"], errors="coerce")
df = df.dropna(subset=["data", "local_lat", "local_lon"])


if __name__ == "__main__":
    baixar_e_formatar_csv()
    time.sleep(3)
    df_geral = detectar_clusters(df)
    print("Clusters detectados (geral):")
    print(df_geral[["cluster", "diagnostico", "data", "local_lat", "local_lon","nome"]]
          .to_string(index=False))
    gerar_grafico_geral(df_geral)
    gerar_graficos_pizza(df_geral)
    #Verifica se tem data
    if len(sys.argv) > 1:
        data_ref = sys.argv[1]
        print(f"Rodando DBSCAN para a data: {data_ref}")
    else:
        data_ref = date.today().strftime("%Y-%m-%d")
    df_data = detectar_surtos_por_data(df, data_ref)
    if not df_data.empty:
        print(f"\nSurtos detectados em torno de {data_ref}:")
        print(df_data[["cluster", "diagnostico", "data", "local_lat", "local_lon", "nome"]]
              .to_string(index=False))
        gerar_grafico_tempo(df_data, data_ref=data_ref)
    print(f"\nGráficos salvos em: {imagens_path}")
    # Gerar mapa interativo
    gerar_mapa_clusters(df_geral, arquivo_saida="mapa_clusters.html")
    gerar_mapa_clusters_validos(df_geral, arquivo_saida="mapa_clusters_validos.html")
