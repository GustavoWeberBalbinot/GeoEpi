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
        # ---------------------------
        # Gráfico de clusters
        # ---------------------------
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

        # ---------------------------
        # Gráfico de barras coloridas
        # ---------------------------
        contagem_doencas = df_plot['diagnostico'].value_counts()
        plt.figure(figsize=(8,6))

        cores_barras = [cores_doencas.get(doenca, 'gray') for doenca in contagem_doencas.index]

        bars = contagem_doencas.plot(kind='bar', color=cores_barras, edgecolor='black')
        plt.xlabel('Diagnóstico')
        plt.ylabel('Quantidade de casos')
        plt.title('Quantidade total de casos por diagnóstico')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(imagens_path, "barras_geral.png"))
        plt.close()

    elif tipo == "data" and subset is not None:
        df_plot = subset
        # ---------------------------
        # Gráfico de clusters por data
        # ---------------------------
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

        # ---------------------------
        # Gráfico de barras coloridas por data
        # ---------------------------
        contagem_doencas = df_plot['diagnostico'].value_counts()
        plt.figure(figsize=(8,6))

        cores_barras = [cores_doencas.get(doenca, 'gray') for doenca in contagem_doencas.index]

        bars = contagem_doencas.plot(kind='bar', color=cores_barras, edgecolor='black')
        plt.xlabel('Diagnóstico')
        plt.ylabel('Quantidade de casos')
        plt.title(f'Casos entre {data_ref.date()} ± {janela_dias} dias')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(imagens_path, "barras_data.png"))
        plt.close()

# ---------------------------
# Função: mapa interativo de clusters
# ---------------------------
def gerar_mapa_clusters(df, arquivo_saida="mapa_clusters.html"):
    """
    Gera mapa interativo com clusters coloridos por doença.
    """
    cores_doencas = {
        'Dengue': 'orange',
        'COVID': 'red',
        'Influenza': 'blue',
        'Zika': 'green'
    }

    base_path = os.path.dirname(__file__)
    caminho_arquivo = os.path.join(base_path, arquivo_saida)

    lat_media = df['local_lat'].mean()
    lon_media = df['local_lon'].mean()
    mapa = folium.Map(location=[lat_media, lon_media], zoom_start=12)

    for _, row in df.iterrows():
        diagnostico = row["diagnostico"]
        cor = cores_doencas.get(diagnostico, "gray")

        folium.Circle(
            location=[row['local_lat'], row['local_lon']],
            radius=700,
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=0.4,
            popup=f"{diagnostico} (Cluster {row['cluster']})"
        ).add_to(mapa)

    mapa.save(caminho_arquivo)
    print(f"Mapa interativo salvo em {caminho_arquivo}")
    return caminho_arquivo

# ---------------------------
# Função: mapa apenas com clusters válidos
# ---------------------------
def gerar_mapa_clusters_validos(df, arquivo_saida="mapa_clusters_validos.html"):
    """
    Gera um mapa apenas com clusters válidos (exclui ruído, cluster = -1)
    """
    df_validos = df[df["cluster"] != -1].copy()
    if not df_validos.empty:
        print(f"Gerando mapa apenas com clusters válidos ({len(df_validos)} pontos)...")
        gerar_mapa_clusters(df_validos, arquivo_saida=arquivo_saida)
    else:
        print("Nenhum cluster válido encontrado para gerar o mapa.")
