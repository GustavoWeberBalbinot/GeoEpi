import requests
import os
import csv
from dotenv import load_dotenv
from datetime import datetime

# Carrega a URL do .env
load_dotenv()
url = os.getenv("GOOGLE_SHEET_URL")

# Dicionário de bairros e coordenadas
bairro_coords = {
    "Centro": [-23.550520, -46.633308],
    "Zona Norte": [-23.533773, -46.675211],
    "Zona Sul": [-23.634915, -46.700720],
    "Boa Vista": [-26.2903, -48.8451],
    "Saguaçu": [-26.3039, -48.8741],
    "Boehmerwald": [-26.3353, -48.8214],
    "Comerciário": [-26.3212, -48.8456],
    "Iririú": [-26.3143, -48.8652],
    "Petrópolis": [-26.3021, -48.8669],
    "Anita Garibaldi": [-26.3190, -48.8727]
}

def baixar_e_formatar_csv():
    # Caminho direto para a pasta onde o arquivo será salvo
    pasta_destino = os.path.join(os.getcwd(), "python_scripts")

    # Caminho completo do arquivo
    arquivo_csv = os.path.join(pasta_destino, "dados_pacientes.csv")

    # Baixando o conteúdo do CSV
    print(f"Baixando CSV da URL: {url}")
    response = requests.get(url)

    # Verificando se o download foi bem-sucedido
    if response.status_code == 200:
        print("Download do CSV bem-sucedido. Processando dados...")

        # Processa os dados CSV
        content = response.content.decode('utf-8').splitlines()

        # Lê os dados do CSV
        reader = csv.reader(content)
        dados_formatados = []

        # Ignora o cabeçalho do CSV
        next(reader)  # Pula a primeira linha que é o cabeçalho

        # Cria um novo cabeçalho no formato correto
        header = ['idade', 'genero', 'peso', 'altura', 'local_lat', 'local_lon', 'data', 'diagnostico']
        dados_formatados.append(header)  # Adiciona o cabeçalho no formato desejado

        # Processa cada linha de dados
        for row in reader:
            idade = row[1]  # Coluna Idade
            genero = row[2]  # Coluna Gênero
            peso = row[3]  # Coluna Peso
            altura = row[4]  # Coluna Altura
            bairro = row[5]  # Coluna Localização
            diagnostico = row[6]  # Coluna Diagnóstico

            # Formata a data
            data_formatada = datetime.now().strftime('%Y-%m-%d')

            # Obtém latitude e longitude do dicionário de bairros
            coords = bairro_coords.get(bairro, [None, None])
            latitude = coords[0]
            longitude = coords[1]

            # Monta a linha formatada
            linha_formatada = [idade, genero, peso, altura, latitude, longitude, data_formatada, diagnostico]

            dados_formatados.append(linha_formatada)

        # Tenta salvar os dados formatados no arquivo CSV
        try:
            print(f"Salvando os dados formatados no arquivo: {arquivo_csv}")
            with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(dados_formatados)
            print(f"Arquivo CSV atualizado com sucesso: {arquivo_csv}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo CSV: {e}")
    else:
        print(f"Erro ao tentar baixar o arquivo. Status code: {response.status_code}")

baixar_e_formatar_csv()
