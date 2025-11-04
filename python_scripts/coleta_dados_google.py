import requests
import os
import csv
import random
from dotenv import load_dotenv
from datetime import datetime

# Carrega a URL do .env
load_dotenv()
url = os.getenv("GOOGLE_SHEET_URL")

bairro_coords = {
    "Centro de Joinville": [
        [-26.3044, -48.8487],
        [-26.3300, -48.8300],
        [-26.2800, -48.8700]
    ],
    "Zona Norte": [
        [-26.2777, -48.8478],
        [-26.2520, -48.8200],
        [-26.3000, -48.8700]
    ],
    "Zona Sul": [
        [-26.3530, -48.8480],
        [-26.3800, -48.8700],
        [-26.3400, -48.8200]
    ],
    "Boa Vista": [
        [-26.2920, -48.8350],
        [-26.2700, -48.8200],
        [-26.3100, -48.8700]
    ],
    "Saguaçu": [
        [-26.3039, -48.8741],
        [-26.2800, -48.8500],
        [-26.3250, -48.8950]
    ],
    "Boehmerwald": [
        [-26.3353, -48.8214],
        [-26.3600, -48.8000],
        [-26.3100, -48.8400]
    ],
    "Comerciário": [
        [-26.3350, -48.8500],
        [-26.3450, -48.8700],
        [-26.2950, -48.8200]
    ],
    "Iririú": [
        [-26.3143, -48.8652],
        [-26.2900, -48.8400],
        [-26.3350, -48.8900]
    ],
    "Petrópolis": [
        [-26.2950, -48.8550],
        [-26.2800, -48.8400],
        [-26.3250, -48.8900]
    ],
    "Anita Garibaldi": [
        [-26.3190, -48.8727],
        [-26.2950, -48.8500],
        [-26.3400, -48.8950]
    ]
}

def baixar_e_formatar_csv():
    # Caminhos
    pasta_destino = os.path.join(os.getcwd(), "python_scripts")
    arquivo_csv = os.path.join(pasta_destino, "dados_pacientes.csv")
    response = requests.get(url)
    
    # Verificando se o download foi bem-sucedido
    if response.status_code == 200:
        content = response.content.decode('utf-8').splitlines()
        reader = csv.reader(content)
        dados_formatados = []
        next(reader)
        header = ['nome', 'idade', 'genero', 'peso', 'altura', 'local_lat', 'local_lon', 'data', 'diagnostico']
        dados_formatados.append(header)
        # Processar cada linha
        for row in reader:
            nome = row[1]
            idade = row[2]
            genero = row[3]
            peso = row[4]
            altura = row[5]
            bairro = row[6]
            diagnostico = row[7]
            data_formatada = datetime.now().strftime('%Y-%m-%d')
            coords_list = bairro_coords.get(bairro)
            if coords_list:
                latitude, longitude = coords_list[0]
            else:
                latitude, longitude = [None, None]
            linha_formatada = [nome, idade, genero, peso, altura, latitude, longitude, data_formatada, diagnostico]
            dados_formatados.append(linha_formatada)
        # Salvar CSV
        try:
            print(f"Salvando os dados formatados no arquivo: {arquivo_csv}")
            os.makedirs(pasta_destino, exist_ok=True)
            with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(dados_formatados)
            print(f"Arquivo CSV atualizado com sucesso: {arquivo_csv}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo CSV: {e}")
    else:
        print(f"Erro ao tentar baixar o arquivo. Status code: {response.status_code}")

baixar_e_formatar_csv()
