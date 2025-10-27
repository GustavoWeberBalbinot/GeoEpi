async function rodarDBSCAN() {
  const resp = await fetch("/rodar_dbscan");
  const json = await resp.json();
  document.getElementById("saida").innerText = json.saida || json.erro;
  atualizarMapa("geral");
}

async function rodarDBSCANporData() {
  const data_ref = document.getElementById("data_filtro").value;
  if (!data_ref) return alert("Escolha uma data!");
  const resp = await fetch("/rodar_dbscan_data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data_ref })
  });
  const json = await resp.json();
  document.getElementById("saida").innerText = json.saida || json.erro;
  atualizarMapa("data");
}

function atualizarMapa(tipo) {
  const mapa = document.getElementById("mapa_" + tipo);
  mapa.src = "/mapa?rand=" + Math.random();
  mapa.style.display = "block";
}
