from coleta_dados_google import adicionar_no_csv
from flask import Flask, request, render_template, jsonify, send_file, Response
import pandas as pd
import subprocess
import os
import time
import threading
import datetime
import socket
import qrcode

app = Flask(__name__)
lock = threading.Lock()

BASE = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE, "dados_pacientes.csv")
MAIN_PATH = os.path.join(BASE, "main.py")
IMAGENS_PATH = os.path.join(BASE, "imagens")
MAPA_PATH = os.path.join(BASE, "mapa_clusters.html")
BOLINHAS_PATH = os.path.join(BASE, "bolinhas.html")
LOG_FILE = "saida_python.log"
CAMINHO_QR = os.path.join(IMAGENS_PATH, "QR_GeoEpi.png")


if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=["idade","genero","peso","altura","local_lat","local_lon","data","diagnostico"]).to_csv(CSV_PATH, index=False)



def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Não envia nada, apenas testa rota
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


ip_local = get_local_ip()
url = f"http://{ip_local}:5000"

# Gera o QR Code
os.makedirs(IMAGENS_PATH, exist_ok=True)
img = qrcode.make(url)
img.save(CAMINHO_QR)



def rodar_main_periodicamente():
    """Executa o main.py a cada 15 seg"""
    while True:
        try:
            result = subprocess.run(["python", MAIN_PATH],
                                    capture_output=True,
                                    text=True,
                                    check=True)
            print("main.py executado com sucesso:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Erro ao executar main.py:", e.stderr)
        time.sleep(15)

# Inicia a execução periódica do main.py em uma thread separada
thread = threading.Thread(target=rodar_main_periodicamente, daemon=True)
thread.start()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/main")
def main():
    return render_template("main.html")


@app.route("/barras")
def barras():
    return render_template("barras.html")


@app.route("/bolinhas")
def cluster():
    return render_template("bolinhas.html")


@app.route("/pythonsaida")
def pagina_saida_python():
    return render_template("pythonsaida.html")


@app.route("/dados")
def dados():
    return render_template("dados.html")


@app.route("/enviar_dados", methods=["POST"])
def enviar_dados():
    try:
        dados = request.get_json()
        campos_obrigatorios = ["nome", "idade", "genero", "peso", "altura", "bairro", "data", "diagnostico"]
        for campo in campos_obrigatorios:
            if campo not in dados or str(dados[campo]).strip() == "":
                return jsonify({"erro": f"Campo obrigatório ausente: {campo}"}), 400
        try:
            datetime.datetime.strptime(dados["data"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"erro": "Formato de data inválido. Use AAAA-MM-DD."}), 400
        with lock:
            adicionar_no_csv(dados)
        return jsonify({"mensagem": "Dados salvos com sucesso!"}), 200
    
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    


@app.route("/rodar_dbscan", methods=["GET"])
def rodar_dbscan():
    try:
        result = subprocess.run(["python", MAIN_PATH],
                                capture_output=True,
                                text=True,
                                check=True)
        return jsonify({"saida": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"erro": e.stderr}), 500


@app.route("/rodar_dbscan_data", methods=["POST"])
def rodar_dbscan_data():
    """Executa o DBSCAN filtrado por data"""
    data_ref = request.json.get("data_ref")
    if not data_ref:
        return jsonify({"erro": "Data não fornecida"}), 400

    try:
        result = subprocess.run(
            ["python", MAIN_PATH, data_ref],
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({"saida": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"erro": e.stderr}), 500



@app.route("/grafico/<tipo>")
def grafico(tipo):
    """
    tipo: cluster_geral, barras_geral, cluster_data, barras_data,
          pizza_covid, pizza_zika, pizza_dengue, pizza_influenza
    """
    path = os.path.join(IMAGENS_PATH, f"{tipo}.png")

    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    else:
        return f"Gráfico {tipo} ainda não gerado", 404

#Rotas do mapa

@app.route("/mapa")
def exibir_mapa():
    """Exibe o mapa interativo gerado pelo DBSCAN"""
    if os.path.exists(MAPA_PATH):
        return send_file(MAPA_PATH)
    else:
        return "Mapa ainda não gerado.", 404


@app.route("/mapa_validos")
def exibir_mapa_validos():
    """Exibe o mapa interativo apenas com clusters válidos"""
    path = os.path.join(BASE, "mapa_clusters_validos.html")
    if os.path.exists(path):
        return send_file(path)
    else:
        return "Mapa de clusters válidos ainda não gerado.", 404

#Saida log

@app.route("/saida_python")
def saida_python():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            conteudo = f.read()
        return Response(conteudo, mimetype="text/plain")
    except FileNotFoundError:
        return Response("Nenhuma saída registrada ainda.", mimetype="text/plain")

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=False)# CMD ipconfig