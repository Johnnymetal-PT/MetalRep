function calcular_xbslog_nacional(destino, dimensoes, conversion) {
    let totalCubicMeters = 0;
    let totalLdm = 0;
    let mensagens = [];

    let onlyPallets = true;
    let allPalletsHigh = true;
    let allLengthsValid = true;
    let existePalletAlta = false;
    let existePalletBaixa = false;
    let existeBox = false;

    // Verifica condições para LDM e mistura de tipos
    dimensoes.forEach(d => {
        if (d.type !== "pallet") onlyPallets = false;
        if (d.type === "pallet") {
            if (d.height <= 125) allPalletsHigh = false;
            if (d.height > 125) existePalletAlta = true;
            if (d.height <= 125) existePalletBaixa = true;
            if (d.length < 100 || d.length > 125) allLengthsValid = false;
        }
        if (d.type === "box") existeBox = true;
    });

    let totalWeight, scaledWeight, rates, rateValue, rateLabel, cost;

    // 1. Cálculo por LDM (caso especial)
    if (onlyPallets && allPalletsHigh) {
        if (!allLengthsValid) {
            return { erro: "Palete com o comprimento fora de medida, não é possivel calcular!!!" };
        }

        mensagens.push("Cálculo feito por LDM porque todas as paletes têm altura superior a 125cm e comprimento entre 100 e 125cm.");

        dimensoes.forEach(d => {
            // Para cada palete, usar sempre comprimento 120
            let adjustedLength = 120;
            totalLdm += (d.width / 240) * (adjustedLength / 100) * d.quantity;
        });

        if (totalLdm === 0) {
            return { erro: "Não é possível calcular: Nenhuma dimensão LDM válida." };
        }
        totalWeight = totalLdm * (conversion?.LDM || 333);

    } else {
        // 2. Cálculo por m3 (todas as outras situações)
        dimensoes.forEach(d => {
            if (d.type === "pallet" && d.height > 125) existePalletAlta = true;
            if (d.type === "pallet" && d.height <= 125) existePalletBaixa = true;
            if (d.type === "box") existeBox = true;

            let adjustedHeight = d.height;
            // Se for palete alta (>125), força altura 250cm
            if (d.type === "pallet" && d.height > 125) {
                adjustedHeight = 250;
            }
            // Caixas e paletes baixas usam altura original
            let cubicMeters = (d.width * d.length * adjustedHeight) / 1000000;
            totalCubicMeters += cubicMeters * d.quantity;
        });

        if (totalCubicMeters === 0) {
            return { erro: "Por favor preencha as dimensões." };
        }

        totalWeight = totalCubicMeters * (conversion?.m3 || 333);

        // Mensagens explicativas dinâmicas
        if (existePalletAlta && (existePalletBaixa || existeBox)) {
            mensagens.push("Embora uma ou mais paletes tenham altura superior a 125cm, o cálculo foi feito por m³ porque há mistura de tipos (paletes altas com paletes baixas e/ou caixas). Nestes casos, as paletes altas são consideradas com altura de 250cm.");
        } else if (existePalletBaixa && !existePalletAlta) {
            mensagens.push("O cálculo foi feito por m³ porque existem apenas paletes baixas (≤ 125cm) ou caixas.");
        } else if (existeBox && !existePalletAlta && !existePalletBaixa) {
            mensagens.push("O cálculo foi feito por m³ porque existem caixas nas linhas.");
        } else if (existePalletAlta && !existePalletBaixa && !existeBox) {
            mensagens.push("O cálculo foi feito por m³ porque as dimensões das paletes não permitem o cálculo por LDM.");
        }
    }

    // Tarifário nacional
    rates = destino?.rates;
    if (!rates) {
        return { erro: "Não existem tarifas para este destino nacional." };
    }

    // Faixas tarifárias (mantém sua lógica original)
    if (totalWeight <= 50) {
        scaledWeight = 1;
        rateValue = rates["1-50"];
        cost = rates["1-50"];
        rateLabel = "1-50";
    } else if (totalWeight <= 100) {
        scaledWeight = 1;
        rateValue = rates["51-100"];
        cost = rates["51-100"];
        rateLabel = "51-100";
    } else if (totalWeight <= 200) {
        scaledWeight = Math.ceil(totalWeight / 100);
        rateValue = rates["101-200"];
        cost = scaledWeight * rates["101-200"];
        rateLabel = "101-200";
    } else if (totalWeight <= 300) {
        scaledWeight = Math.ceil(totalWeight / 100);
        rateValue = rates["201-300"];
        cost = scaledWeight * rates["201-300"];
        rateLabel = "201-300";
    } else if (totalWeight <= 500) {
        scaledWeight = Math.ceil(totalWeight / 100);
        rateValue = rates["301-500"];
        cost = scaledWeight * rates["301-500"];
        rateLabel = "301-500";
    } else if (totalWeight <= 750) {
        scaledWeight = totalWeight <= 700 ? Math.ceil(totalWeight / 100) : 7;
        rateValue = rates["501-750"];
        cost = scaledWeight * rates["501-750"];
        rateLabel = "501-750";
    } else if (totalWeight <= 1000) {
        scaledWeight = totalWeight <= 800 ? 8 : Math.ceil(totalWeight / 100);
        rateValue = rates["751-1000"];
        cost = scaledWeight * rates["751-1000"];
        rateLabel = "751-1000";
    } else if (totalWeight <= 2000) {
        scaledWeight = Math.ceil(totalWeight / 100);
        rateValue = rates["1001-2000"];
        cost = scaledWeight * rates["1001-2000"];
        rateLabel = "1001-2000";
    } else if (totalWeight <= 3500) {
        scaledWeight = Math.ceil(totalWeight / 100);
        rateValue = rates["2001-3500"];
        cost = scaledWeight * rates["2001-3500"];
        rateLabel = "2001-3500";
    } else if (totalWeight <= 5000) {
        scaledWeight = Math.ceil(totalWeight / 100);
        rateValue = rates["3501-5000"];
        cost = scaledWeight * rates["3501-5000"];
        rateLabel = "3501-5000";
    } else {
        scaledWeight = Math.ceil(totalWeight / 100);
        rateValue = rates[">5000"];
        cost = scaledWeight * rates[">5000"];
        rateLabel = ">5000";
    }
    cost = cost < rates.minimum ? rates.minimum : cost;

    // Mensagem condicional baseada no peso (opcional para nacional, ajuste conforme necessário)
    if (totalWeight <= 2500) {
        mensagens.push("Entrega prevista por agente local (peso tarifário ≤ 2500kg).");
    } else {
        mensagens.push("Valores apresentados para entrega direta (peso tarifário > 2500kg).");
    }

    // Exemplo de mensagem extra para zonas específicas (ajuste conforme necessário)
    if (
        destino?.country &&
        destino.country.toLowerCase() === "portugal" &&
        (destino.code === "acores" || destino.code === "madeira")
    ) {
        mensagens.push("Atenção: Para as ilhas dos Açores e Madeira, podem ser aplicadas taxas adicionais.");
    }

    return {
        transportadora: "XBS Nacional",
        totalLdm,
        totalCubicMeters,
        totalWeight,
        scaledWeight,
        rateValue,
        rateLabel,
        cost,
        erro: null,
        mensagens
    };
}
