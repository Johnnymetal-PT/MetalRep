function validateInput(input) {
    input.value = input.value.replace(/\D/g, '');

    if (input.value.length > 3) {
        input.value = input.value.slice(0, 3);
    }
}

function finalCalculate() {
    // --- INTEGRAÇÃO: Valida país e zona antes de tudo ---
    const countryInput = document.getElementById('country').value;
    const zoneInput = document.getElementById('zone').value;

    // Função para verificar se o valor existe no dropdown (usa a tua lógica de normalização, se necessário)
    function existeNoDropdown(inputId, listId) {
        const input = document.getElementById(inputId);
        const list = document.getElementById(listId);
        if (!input || !list) return false;
        const valorInput = input.value.trim().toLowerCase();
        const opcoes = Array.from(list.querySelectorAll('a'));
        return opcoes.some(opt => opt.textContent.trim().toLowerCase() === valorInput);
    }

    const countryValid = existeNoDropdown('country', 'country-list');
    const zoneValid = existeNoDropdown('zone', 'zone-list');


    // --- O resto da função mantem-se como já tens ---
    const lines = document.querySelectorAll(".dimension-line");
    let allValid = true;

    lines.forEach((line) => {
        const width = line.querySelector(".width");
        const length = line.querySelector(".length");
        const height = line.querySelector(".height");
        const quantity = line.querySelector(".quantity");
        const type = line.querySelector(".type");

        if (!width.value) {
            highlightField(width);
            allValid = false;
        } else {
            removeHighlight(width);
        }

        if (!length.value) {
            highlightField(length);
            allValid = false;
        } else {
            removeHighlight(length);
        }

        if (!height.value) {
            highlightField(height);
            allValid = false;
        } else {
            removeHighlight(height);
        }

        if (!quantity.value) {
            highlightField(quantity);
            allValid = false;
        } else {
            removeHighlight(quantity);
        }

        if (!type.value) {
            highlightField(type);
            allValid = false;
        } else {
            removeHighlight(type);
        }
    });

    const errorMessage = document.getElementById("error-message");
    if (!allValid) {
        errorMessage.textContent = "Please fill in all the required fields.";
    } else {
        errorMessage.textContent = "";
        calculateResults(); // Chama a função dinâmica
    }
}

function highlightField(field) {
    field.classList.add("highlight");
}

function removeHighlight(field) {
    field.classList.remove("highlight");
}
