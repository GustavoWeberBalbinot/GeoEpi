import os
import csv
import random
import requests
from datetime import datetime
from dotenv import load_dotenv
import re
import time

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
    pasta_destino = os.path.join(os.getcwd(), "python_scripts")
    os.makedirs(pasta_destino, exist_ok=True)
    arquivo_csv = os.path.join(pasta_destino, "dados_pacientes.csv")

    #Baixa do Google
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[ERRO] Falha ao baixar o CSV. Status code: {response.status_code}")
        return

    content = response.content.decode('utf-8').splitlines()
    reader = csv.reader(content)
    next(reader, None)  # ignora o cabeçalho do Google Forms
    linhas_novas_brutas = list(reader)

    #Conta as linhas
    if os.path.exists(arquivo_csv):
        with open(arquivo_csv, "r", encoding="utf-8") as f:
            leitor = csv.reader(f)
            linhas_atuais = list(leitor)[1:]  # ignora cabeçalho
    else:
        linhas_atuais = []

    num_linhas_atuais = len(linhas_atuais)
    num_linhas_novas = len(linhas_novas_brutas)
    diferenca = num_linhas_novas - num_linhas_atuais

    if diferenca <= 0:
        print("[INFO] Nenhuma nova linha encontrada.")
        return

    #Formatação
    novas_formatadas = []
    for row in linhas_novas_brutas[-diferenca:]:
        nome = row[1]
        nome_limpo = re.sub(r'[^A-Za-zÀ-ÿ0-9 ]+', ' ', nome).strip()
        idade = row[2]
        genero = row[3]
        peso = row[4]
        altura = row[5]
        bairro = row[6]
        diagnostico = row[7]
        data_formatada = datetime.now().strftime('%Y-%m-%d')

        coords_list = bairro_coords.get(bairro)
        if coords_list:
            latitude, longitude = random.choice(coords_list)
        else:
            latitude, longitude = [None, None]

        novas_formatadas.append([
            nome_limpo, idade, genero, peso, altura, latitude, longitude, bairro, data_formatada, diagnostico
        ])

    header = ['nome', 'idade', 'genero', 'peso', 'altura',
              'local_lat', 'local_lon', 'bairro', 'data', 'diagnostico']

    if not os.path.exists(arquivo_csv):
        with open(arquivo_csv, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            f.write("\n")

    # Garante que as novas linhas sejam salvas
    with open(arquivo_csv, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(novas_formatadas)
        f.flush()
        os.fsync(f.fileno())
    time.sleep(1)


