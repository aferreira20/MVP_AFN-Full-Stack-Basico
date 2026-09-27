/**
 * API client: one function per route of the Charge Fácil API.
 * Every call is logged in the on-screen API monitor (see ui.js).
 */
const Api = (() => {
  // Build a query string, skipping empty values
  function qs(params = {}) {
    const busca = new URLSearchParams();
    Object.entries(params).forEach(([chave, valor]) => {
      if (valor !== undefined && valor !== null && valor !== "") busca.append(chave, valor);
    });
    const texto = busca.toString();
    return texto ? `?${texto}` : "";
  }

  // Turn API error payloads (ours or pydantic's 422 list) into a readable message
  function mensagemDeErro(status, dados) {
    if (dados && dados.mensagem) return dados.mensagem;
    if (Array.isArray(dados) && dados.length) {
      const campos = dados.map((e) => (e.loc || []).slice(-1)[0]).filter(Boolean);
      return `Dados inválidos${campos.length ? `: verifique ${campos.join(", ")}` : ""}`;
    }
    return `Erro inesperado (HTTP ${status})`;
  }

  async function requisitar(metodo, caminho, corpo) {
    const opcoes = { method: metodo, headers: {} };
    if (corpo !== undefined) {
      opcoes.headers["Content-Type"] = "application/json";
      opcoes.body = JSON.stringify(corpo);
    }

    let resposta;
    try {
      resposta = await fetch(API_URL + caminho, opcoes);
    } catch (erroRede) {
      Monitor.registrar(metodo, caminho, "OFF");
      UI.statusApi(false);
      throw new Error(`Não foi possível conectar à API em ${API_URL}. Ela está rodando?`);
    }

    UI.statusApi(true);
    Monitor.registrar(metodo, caminho, resposta.status);
    const dados = await resposta.json().catch(() => null);
    if (!resposta.ok) throw new Error(mensagemDeErro(resposta.status, dados));
    return dados;
  }

  return {
    // Dashboard
    dashboard: () => requisitar("GET", "/dashboard"),

    // Stations
    listarEstacoes: (filtros) => requisitar("GET", `/estacoes${qs(filtros)}`),
    buscarEstacao: (id) => requisitar("GET", `/estacoes/${id}`),
    cadastrarEstacao: (dados) => requisitar("POST", "/estacoes", dados),
    atualizarEstacao: (id, dados) => requisitar("PUT", `/estacoes/${id}`, dados),
    removerEstacao: (id) => requisitar("DELETE", `/estacoes/${id}`),

    // Power banks
    listarPowerBanks: (filtros) => requisitar("GET", `/powerbanks${qs(filtros)}`),
    adicionarPowerBank: (dados) => requisitar("POST", "/powerbanks", dados),
    alterarStatusPowerBank: (id, status) => requisitar("PATCH", `/powerbanks/${id}/status`, { status }),
    removerPowerBank: (id) => requisitar("DELETE", `/powerbanks/${id}`),
    // estacaoId = null sends the power bank back to stock
    alocarPowerBank: (id, estacaoId) => requisitar("PATCH", `/powerbanks/${id}/estacao`, { estacao_id: estacaoId }),

    // Rentals (self-service totem)
    listarAlugueis: (filtros) => requisitar("GET", `/alugueis${qs(filtros)}`),
    iniciarAluguel: (dados) => requisitar("POST", "/alugueis", dados),
    devolverPowerBank: (aluguelId, estacaoId) =>
      requisitar("PATCH", `/alugueis/${aluguelId}/devolucao`, { estacao_id: estacaoId }),
  };
})();
