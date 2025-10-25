from flask import Flask, request, render_template, jsonify, send_file
import pandas as pd
import subprocess
import os

app = Flask(__name__)

BASE = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE, "dados_pacientes.csv")

# cria CSV se não existir
if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=["idade","genero","peso","altura","local_lat","local_lon","data","diagnostico"]).to_csv(CSV_PATH, index=False)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/enviar_dados", methods=["POST"])
def enviar_dados():
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    df = pd.read_csv(CSV_PATH)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)
    return jsonify({"mensagem": "Dados adicionados ao CSV com sucesso!"})


@app.route("/rodar_dbscan", methods=["GET"])
def rodar_dbscan():
    try:
        # Caminho absoluto para o dbscan.py
        dbscan_path = os.path.join(BASE, "dbscan.py")
        result = subprocess.run(["python", dbscan_path],
                                capture_output=True,
                                text=True,
                                check=True)
        return jsonify({"saida": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"erro": e.stderr}), 500

    
@app.route("/grafico")
def grafico():
    path = os.path.join(BASE, "imagens", "cluster.png")
    if os.path.exists(path):
        return send_file(path, mimetype='image/png')
    else:
        return "Gráfico ainda não gerado", 404
    
@app.route("/grafico_barras")
def grafico_barras():
    path = os.path.join(BASE, "imagens", "barras_doencas.png")
    if os.path.exists(path):
        return send_file(path, mimetype='image/png')
    else:
        return "Gráfico ainda não gerado", 404


if __name__ == "__main__":
    app.run(debug=True)
