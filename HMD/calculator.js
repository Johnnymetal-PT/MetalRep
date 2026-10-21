function calculateResults() {
    const lines = document.querySelectorAll(".dimension-line");
    let totalCubicMeters = 0;
    let totalLdm = 0;
    let hasBox = false;
    let hasPallet = false;
    let allPalletsHaveLowHeight = true;
    let allPalletsHaveHighHeight = true;
    let allLengthsValid = true;
    const result = document.getElementById("result");

    lines.forEach((line) => {
        const type = line.querySelector(".type").value;
        const height = parseFloat(line.querySelector(".height").value) || 0;
        const length = parseFloat(line.querySelector(".length").value) || 0;

        if (type === "box") {
            hasBox = true;
        } else if (type === "pallet") {
            hasPallet = true;
            if (height > 125) {
                allPalletsHaveLowHeight = false;
                if (length < 100 || length > 125) {
                    allLengthsValid = false;
                }
            } else {
                allPalletsHaveHighHeight = false;
            }
        }
    });

    const country = document.getElementById("country").value;
    const zone = document.getElementById("zone").value;

    if (!country || !zone) {
        result.textContent = "Please select a country and zone.";
        return;
    }

    const isTransportInternational = isInternational(country, zone);

    const conversionFactors = isTransportInternational
        ? conversionFactorsInternational
        : conversionFactorsNational;

    let totalWeight, scaledWeight, rates, rateTier, cost, rateValue;

    if (hasPallet && !hasBox && allPalletsHaveHighHeight && allLengthsValid) {
        lines.forEach((line) => {
            const type = line.querySelector(".type").value;
            const width = parseFloat(line.querySelector(".width").value) || 0;
            const length = parseFloat(line.querySelector(".length").value) || 0;
            const quantity = parseInt(line.querySelector(".quantity").value, 10) || 0;
            const volumetricWeightField = line.querySelector(".cubic-capacity");

            if (type === "pallet") {
                const adjustedLength = (length >= 100 && length <= 125) ? 120 : length;
                totalLdm += (width / 240) * (adjustedLength / 100) * quantity;
                volumetricWeightField.value = "LDM";
            }
        });

        if (totalLdm === 0) {
            result.textContent = "Cannot calculate: No valid LDM dimensions.";
            return;
        }

        totalWeight = totalLdm * conversionFactors.LDM;
    } else {
        lines.forEach((line) => {
            const type = line.querySelector(".type").value;
            const width = parseFloat(line.querySelector(".width").value) || 0;
            const length = parseFloat(line.querySelector(".length").value) || 0;
            const height = parseFloat(line.querySelector(".height").value) || 0;
            const quantity = parseInt(line.querySelector(".quantity").value, 10) || 0;
            const cubicCapacityField = line.querySelector(".cubic-capacity");

            if (type === "box") {
                const cubicMeters = (width * length * height) / 1000000;
                const totalForLine = cubicMeters * quantity;
                totalCubicMeters += totalForLine;
                cubicCapacityField.value = totalForLine.toFixed(3);
            } else if (type === "pallet") {
                const adjustedLength = (length >= 100 && length <= 125) ? 120 : length;
                const adjustedHeight = height > 125 ? 250 : height;
                const cubicMeters = (width * adjustedLength * adjustedHeight) / 1000000;
                const totalForLine = cubicMeters * quantity;
                totalCubicMeters += totalForLine;
                cubicCapacityField.value = totalForLine.toFixed(3);
            }
        });

        if (totalCubicMeters === 0) {
            result.textContent = "Please fill in dimensions.";
            return;
        }
        totalWeight = totalCubicMeters * conversionFactors.m3;
    }

    rates = supplierData.find((item) => item.country === country && item.code === zone)?.rates;

    if (!rates) {
        result.textContent = "No rates found for the selected country and zone.";
        return;
    }

    if (!isTransportInternational) {
        if (totalWeight <= 50) {
            scaledWeight = 1;
            rateValue = rates["1-50"];
            cost = rates["1-50"];
        } else if (totalWeight <= 100) {
            scaledWeight = 1;
            rateValue = rates["51-100"];
            cost = rates["51-100"];
        } else if (totalWeight <= 200) {
            scaledWeight = Math.ceil(totalWeight / 100);
            rateValue = rates["101-200"];
            cost = scaledWeight * rates["101-200"];
        } else if (totalWeight <= 300) {
            scaledWeight = Math.ceil(totalWeight / 100);
            rateValue = rates["201-300"];
            cost = scaledWeight * rates["201-300"];
        } else if (totalWeight <= 500) {
            scaledWeight = Math.ceil(totalWeight / 100);
            rateValue = rates["301-500"];
            cost = scaledWeight * rates["301-500"];
        } else if (totalWeight <= 750) {
            if (totalWeight <= 700) {
                scaledWeight = Math.ceil(totalWeight / 100);
            } else {
                scaledWeight = 7;
            }
            rateValue = rates["501-750"];
            cost = scaledWeight * rates["501-750"];
        } else if (totalWeight <= 1000) {
            if (totalWeight <= 800) {
                scaledWeight = 8;
            } else {
                scaledWeight = Math.ceil(totalWeight / 100);
            }
            rateValue = rates["751-1000"];
            cost = scaledWeight * rates["751-1000"];
        } else if (totalWeight <= 2000) {
            scaledWeight = Math.ceil(totalWeight / 100);
            rateValue = rates["1001-2000"];
            cost = scaledWeight * rates["1001-2000"];
        } else if (totalWeight <= 3500) {
            scaledWeight = Math.ceil(totalWeight / 100);
            rateValue = rates["2001-3500"];
            cost = scaledWeight * rates["2001-3500"];
        } else if (totalWeight <= 5000) {
            scaledWeight = Math.ceil(totalWeight / 100);
            rateValue = rates["3501-5000"];
            cost = scaledWeight * rates["3501-5000"];
        } else {
            scaledWeight = Math.ceil(totalWeight / 100);
            rateValue = rates[">5000"];
            cost = scaledWeight * rates[">5000"];
        }
    } else {
        const roundedWeight = Math.ceil(totalWeight / 100) * 100;
        scaledWeight = roundedWeight / 100;
        rateTier = getRateTier(totalWeight, rates, isTransportInternational);
        rateValue = rates[rateTier];
        cost = scaledWeight * rateValue;
    }

    cost = cost < rates.minimum ? rates.minimum : cost;

    result.innerHTML = `
        <p>Total ${totalLdm > 0 ? "LDM" : "Cubic Meters"}: ${totalLdm > 0 ? totalLdm.toFixed(2) : totalCubicMeters.toFixed(3)} ${totalLdm > 0 ? "m" : "m³"}</p>
        <p>Total Weight: ${totalWeight.toFixed(2)} kg</p>
        ${isTransportInternational && totalLdm === 0 ? `<p>Rounded Weight: ${Math.ceil(totalWeight / 100) * 100} kg</p>` : ""}
        <p>Scaled Weight: ${scaledWeight}</p>
        <p>Rate Value: €${rateValue ? rateValue.toFixed(2) : "N/A"}</p>
        <p>Final Cost: €${cost.toFixed(2)}</p>
    `;
}

function getRateTier(weight, rates, isInternational) {
    const rateKeys = Object.keys(rates).filter(key => key !== "minimum");

    if (isInternational) {
        const sortedKeys = rateKeys.sort((a, b) => {
            const aValue = a.startsWith('<') ? parseInt(a.slice(1), 10) : a.startsWith('>') ? parseInt(a.slice(1), 10) : Number.MAX_SAFE_INTEGER;
            const bValue = b.startsWith('<') ? parseInt(b.slice(1), 10) : b.startsWith('>') ? parseInt(b.slice(1), 10) : Number.MAX_SAFE_INTEGER;
            return aValue - bValue;
        });

        for (const key of sortedKeys) {
            if (key.startsWith('<')) {
                const max = parseInt(key.slice(1), 10);
                if (weight <= max) {
                    return key;
                }
            } else if (key.startsWith('>')) {
                const min = parseInt(key.slice(1), 10);
                if (weight > min) {
                    return key;
                }
            }
        }
    } else {
        const sortedKeys = rateKeys.sort((a, b) => {
            const aMin = a.includes('-') ? parseInt(a.split('-')[0], 10) : a.startsWith('>') ? parseInt(a.slice(1), 10) : Number.MAX_SAFE_INTEGER;
            const bMin = b.includes('-') ? parseInt(b.split('-')[0], 10) : b.startsWith('>') ? parseInt(b.slice(1), 10) : Number.MAX_SAFE_INTEGER;
            return aMin - bMin;
        });

        for (const key of sortedKeys) {
            if (key.includes('-')) {
                const [min, max] = key.split('-').map(Number);
                if (weight >= min && weight <= max) {
                    return key;
                }
            } else if (key.startsWith('>')) {
                const min = parseInt(key.slice(1), 10);
                if (weight > min) {
                    return key;
                }
            }
        }
    }

    return "minimum";
}
