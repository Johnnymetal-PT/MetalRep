/**
 * Orquestrador dos cálculos automáticos por tabela.
 * Descobre dinamicamente todas as funções globais do tipo calcular_<nome_tabela>.
 * Basta garantir que cada ficheiro de cálculo exporta a função correta.
 */

/**
 * Procura globalmente todas as funções calcular_<nome> e cria o mapping.
 * Exemplo: window.calcular_xbslog_nacional => chave "xbslog_nacional"
 */
function getDynamicCalculoMap() {
  const map = {};
  for (const key in window) {
    if (key.startsWith("calcular_") && typeof window[key] === "function") {
      const nomeTabela = key.replace(/^calcular_/, "");
      map[nomeTabela] = window[key];
    }
  }
  return map;
}

/**
 * Calcula resultados para todas as tabelas disponíveis com cálculo.
 * @param {Array} destinos - [{table, destino}] resultado do dataLoader.
 * @param {Array} dimensoes - Array de linhas do formulário [{type, width, length, height, quantity}]
 * @returns {Array} [{tabela, resultado}]
 */
function calcularParaTodasTabelas(destinos, dimensoes) {
  const calculoMap = getDynamicCalculoMap();
  let resultados = [];
  for (const { table, destino } of destinos) {
    // table.name precisa de estar presente em cada JSON carregado (adapte o loader se necessário)
    const func = calculoMap[table.name];
    if (typeof func === "function") {
      const resultado = func(destino, dimensoes, table.conversion);
      resultados.push({ tabela: table.name, resultado });
    }
  }
  return resultados;
}
