import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster, FeatureGroupSubGroup
from branca.element import Element
from folium import FeatureGroup
import pandas as pd
import os


# Caminhos
base_path = os.path.dirname(__file__)
imagens_path = os.path.join(base_path, "imagens")
csv_path = os.path.join(base_path, "dados_pacientes.csv")

os.makedirs(imagens_path, exist_ok=True)


cores_doencas = {
    'Dengue': 'orange',
    'COVID': 'red',
    'Influenza': 'blue',
    'Zika': 'green'
}

#GRAFICOS GERAIS:

def gerar_grafico_pontos_geral(df):
    plt.figure(figsize=(8, 6))
    for doenca, grupo in df.groupby('diagnostico'):
        cor = cores_doencas.get(doenca, 'gray')
        grupo_cluster = grupo[grupo['cluster'] != -1]
        grupo_ruido = grupo[grupo['cluster'] == -1]

        plt.scatter(
            grupo_cluster['local_lon'], grupo_cluster['local_lat'],
            c=cor, label=f"{doenca} (cluster)",
            alpha=0.7, s=70, edgecolor='black', marker='o'
        )
        plt.scatter(
            grupo_ruido['local_lon'], grupo_ruido['local_lat'],
            c=cor, label=f"{doenca} (isolado)",
            alpha=0.5, s=70, edgecolor='black', marker='x'
        )

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Clusters gerais por doença')
    plt.legend(title='Legenda', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(imagens_path, "cluster_geral.png"), bbox_inches='tight')
    plt.close()



def gerar_grafico_barras_geral(df):
    plt.figure(figsize=(8, 6))
    contagem = df['diagnostico'].value_counts()
    cores_barras = [cores_doencas.get(d, 'gray') for d in contagem.index]

    contagem.plot(kind='bar', color=cores_barras, edgecolor='black')
    plt.xlabel('Diagnóstico')
    plt.ylabel('Quantidade de casos')
    plt.title('Quantidade total de casos por diagnóstico')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(imagens_path, "barras_geral.png"))
    plt.close()

#GRÁFICOS POR TEMPO

def gerar_grafico_pontos_tempo(df, data_ref, janela_dias=30):
    data_ref = pd.to_datetime(data_ref)

    plt.figure(figsize=(8, 6))
    for doenca, grupo in df.groupby('diagnostico'):
        cor = cores_doencas.get(doenca, 'gray')
        grupo_cluster = grupo[grupo['cluster'] != -1]
        grupo_ruido = grupo[grupo['cluster'] == -1]

        plt.scatter(
            grupo_cluster['local_lon'], grupo_cluster['local_lat'],
            c=cor, label=f"{doenca} (cluster)",
            alpha=0.7, s=70, edgecolor='black', marker='o'
        )
        plt.scatter(
            grupo_ruido['local_lon'], grupo_ruido['local_lat'],
            c=cor, label=f"{doenca} (isolado)",
            alpha=0.5, s=70, edgecolor='black', marker='x'
        )

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(f'Clusters detectados ±{janela_dias} dias de {data_ref.date()}')
    plt.legend(title='Legenda', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(imagens_path, "cluster_data.png"), bbox_inches='tight')
    plt.close()


def gerar_grafico_barras_tempo(df, data_ref, janela_dias=30):
    data_ref = pd.to_datetime(data_ref)
    plt.figure(figsize=(8, 6))

    contagem = df['diagnostico'].value_counts()
    cores_barras = [cores_doencas.get(d, 'gray') for d in contagem.index]

    contagem.plot(kind='bar', color=cores_barras, edgecolor='black')
    plt.xlabel('Diagnóstico')
    plt.ylabel('Quantidade de casos')
    plt.title(f'Casos entre {data_ref.date()} ± {janela_dias} dias')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(imagens_path, "barras_data.png"))
    plt.close()



#FUNÇÕES PRINCIPAIS (CHAMADAS NO MAIN)

def gerar_grafico_geral(df):
    gerar_grafico_pontos_geral(df)
    gerar_grafico_barras_geral(df)


def gerar_grafico_tempo(df, data_ref, janela_dias=30):
    gerar_grafico_pontos_tempo(df, data_ref, janela_dias)
    gerar_grafico_barras_tempo(df, data_ref, janela_dias)


#PIZZAS:

def gerar_graficos_pizza(df_resultado):
    for doenca, grupo in df_resultado.groupby('diagnostico'):
        contagem_locais = grupo['bairro'].value_counts()
        if contagem_locais.empty:
            continue
        porcentagens = (contagem_locais / contagem_locais.sum() * 100).round(1)
        plt.figure(figsize=(9, 7))
        wedges, texts = plt.pie(
            contagem_locais,
            startangle=140,
            wedgeprops={'edgecolor': 'black'}
        )
        legend_labels = [
            f"{bairro} — {pct:.1f}%"
            for bairro, pct in zip(contagem_locais.index, porcentagens)
        ]
        plt.legend(
            wedges,
            legend_labels,
            title="Bairros",
            loc="center left",
            bbox_to_anchor=(1.05, 0.5),
            fontsize=13,
            title_fontsize=14,
            labelspacing=1.1
        )
        plt.title(f"Distribuição de {doenca} por bairro", fontsize=16, fontweight='bold')
        plt.tight_layout()
        nome_arquivo = f"pizza_{doenca.lower()}.png"
        plt.savefig(os.path.join(imagens_path, nome_arquivo), bbox_inches='tight')
        plt.close()


#FUNÇÕES MAPA:

def gerar_mapa_clusters(df, arquivo_saida="mapa_clusters.html"):
    """
    Gera mapa interativo com:
      - Menu lateral: apenas 'Doença - Clusters' e 'Doença - Ruído'
      - Cada cluster_id tem seu próprio agrupamento visual
      - Clusters só se unem após certo nível de zoom
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

    for doenca in df['diagnostico'].unique():
        subset = df[df['diagnostico'] == doenca]
        cor = cores_doencas.get(doenca, "gray")

        grupo_clusters = folium.FeatureGroup(name=f"{doenca} - Clusters").add_to(mapa)

        #MarkerCluster separado para cada cluster_id
        subset_validos = subset[subset["cluster"] >= 0]
        for cluster_id in sorted(subset_validos["cluster"].unique()):
            subset_cluster = subset_validos[subset_validos["cluster"] == cluster_id]

            #Cada cluster_id com seu agrupamento próprio
            marker_cluster = MarkerCluster(
                name=f"{doenca} - C{cluster_id}",
                options={'disableClusteringAtZoom': 12}
            ).add_to(grupo_clusters)

            for _, row in subset_cluster.iterrows():
                folium.Circle(
                    location=[row["local_lat"], row["local_lon"]],
                    radius=700,
                    color=cor,
                    fill=True,
                    fill_color=cor,
                    fill_opacity=0.45,
                    popup=f"<b>{doenca}</b><br>Cluster {cluster_id}"
                ).add_to(marker_cluster)

        subset_ruido = subset[subset["cluster"] == -1]
        if not subset_ruido.empty:
            grupo_ruido = folium.FeatureGroup(name=f"{doenca} - Ruído").add_to(mapa)
            for _, row in subset_ruido.iterrows():
                folium.Circle(
                    location=[row["local_lat"], row["local_lon"]],
                    radius=700,
                    color="black",
                    fill=True,
                    fill_color="gray",
                    fill_opacity=0.35,
                    popup=f"<b>{doenca}</b><br>Ruído"
                ).add_to(grupo_ruido)

    folium.LayerControl(collapsed=False).add_to(mapa)

    reload_script = """
    <script>
    setInterval(() => location.reload(), 20000);
    </script>
    """
    mapa.get_root().html.add_child(Element(reload_script))
    mapa.save(caminho_arquivo)
    return caminho_arquivo


def gerar_mapa_clusters_validos(df, arquivo_saida="mapa_clusters_validos.html"):
    """
    Gera um mapa apenas com clusters válidos (exclui ruído, cluster = -1)
    """
    df_validos = df[df["cluster"] != -1].copy()
    if not df_validos.empty:
        gerar_mapa_clusters(df_validos, arquivo_saida=arquivo_saida)
    else:
        print("Nenhum cluster válido encontrado para gerar o mapa.")
