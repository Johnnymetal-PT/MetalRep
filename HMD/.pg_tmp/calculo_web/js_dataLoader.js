let supplierData = [];
let tables = []; // Guardar todos os JSONs carregados aqui

function loadSupplierData() {
  fetch('./Tables/tables-list.json')
    .then(res => res.json())
    .then(tableFiles => Promise.all(
        tableFiles.map(file => fetch(`./Tables/${file}`).then(r => r.json()))
    ))
    .then(loadedTables => {
        tables = loadedTables;
        supplierData = loadedTables.flatMap(table => table.destinations);
        populateCountryDropdown();
    })
    .catch(error => console.error('Error loading supplier data:', error));
}

// Opcional: função para saber se é internacional (ajuste consoante a tua lógica real de tabelas)
function isInternational(country, zone) {
    return supplierData.some(
        (item) => item.country === country && item.code === zone && item.rates["<500kgs"] !== undefined
    );
}
