let batteryChargeState, batteryChargeStateIcon;
let currentState, opHours, batCycles, batDesignCapacity, batMaxChargePower, batMaxDischargePower,
housePower, pvProduction, gridPower, batteryPower, batteryVoltage, batteryCurrent, batteryPercentage,
batteryRemainingTime, houseConsumptionStats, pvProductionStats, batteryChargedStats, batteryDischaredStats,
gridExportStats, gridImportStats;

let color_draining = "#ffe9e9";
let color_charging = "#e9ffe9";

window.addEventListener('DOMContentLoaded', function () {
    initVars();
    //drawTestChart();
    updateHTML();
    setInterval(() => {
        updateHTML();
    }, 2000);
});

function initVars() {
    batteryChargeState = document.querySelector('#batteryChargeState');
    batteryChargeStateIcon = document.querySelector('#batteryChargeStateIcon');

    //currentState = document.querySelector('#currentState');
    opHours = document.querySelector('#opHours');
    batCycles = document.querySelector('#batCycles');
    batDesignCapacity = document.querySelector('#batDesignCapacity');
    batMaxChargePower = document.querySelector('#batMaxChargePower');
    batMaxDischargePower = document.querySelector('#batMaxDischargePower');
    housePower = document.querySelector('#housePower');
    pvProduction = document.querySelector('#pvProduction');
    gridPower = document.querySelector('#gridPower');
    batteryPower = document.querySelector('#batteryPower');
    batteryVoltage = document.querySelector('#batteryVoltage');
    batteryCurrent = document.querySelector('#batteryCurrent');
    batteryPercentage = document.querySelector('#batteryPercentage');
    batteryRemainingTime = document.querySelector('#batteryRemainingTime');
    //houseConsumptionStats = document.querySelector('#houseConsumptionStats');
    //pvProductionStats = document.querySelector('#pvProductionStats');
    //batteryChargedStats = document.querySelector('#batteryChargedStats');
    //batteryDischaredStats = document.querySelector('#batteryDischaredStats');
    //gridExportStats = document.querySelector('#gridExportStats');
    //gridImportStats = document.querySelector('#gridImportStats');
}

function drawTestChart() {
    var ctx = document.getElementById('testChart');
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange', 'Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange', 'Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
            responsive: true,
            datasets: [
                {
                label: '# of Votes',
                fill: 'origin',
                data: [12, 19, 3, 5, 2, 3, 12, 19, 3, 5, 2, 3, 12, 19, 3, 5, 2, 3],
                borderWidth: 1
            }]
        }
    });
}

function updateHTML() {
    /*  */
    fetch("/senec?format=json")
        .then(response => {
            return response.json();
        })
        .then(json => {
            updateHelperHTML(json);
        });
}

function updateHelperHTML(json) {
    /* General - Infocard */
    //currentState.innerHTML = json['general']['current_state'];
    opHours.innerHTML = json['general']['hours_of_operation'] + " h";
    batCycles.innerHTML = json['battery_information']['cycles'];
    batDesignCapacity.innerHTML = json['battery_information']['design_capacity'] + " Wh";
    batMaxChargePower.innerHTML = json['battery_information']['max_charge_power'] + " W";
    batMaxDischargePower.innerHTML = json['battery_information']['max_discharge_power'] + " W";

    /* Consumption and Production */
    housePower.innerHTML = json['live_data']['house_power'].toFixed(2) + " W";
    pvProduction.innerHTML = json['live_data']['pv_production'].toFixed(2) + " W";
    gridPower.innerHTML = json['live_data']['grid_power'].toFixed(2) + " W";
    batteryPower.innerHTML = json['live_data']['battery_charge_power'].toFixed(2) + " W";

    /* Battery */
    if(json['live_data']['battery_charge_power'] > 0) {
        /* Battery charging */
        batteryRemainingTime.innerHTML = "charging";
        if(json['live_data']['battery_percentage'].toFixed(2) < 20.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "red");
        } else if (json['live_data']['battery_percentage'].toFixed(2) < 50.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "yellow");
        } else if (json['live_data']['battery_percentage'].toFixed(2) <= 100.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "green");
        }
    } else {
        /* Battery discharging */
        batteryRemainingTime.innerHTML = getRemainingBatteryDuration(json);
        if(json['live_data']['battery_percentage'].toFixed(2) < 20.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery", 32, "red");
        } else if (json['live_data']['battery_percentage'].toFixed(2) < 50.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-half", 32, "yellow");
        } else if (json['live_data']['battery_percentage'].toFixed(2) <= 100.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-full", 32, "green");
        }
    }
    batteryChargeState.innerHTML = json['live_data']['battery_percentage'].toFixed(2) + " %";
    batteryVoltage.innerHTML = json['live_data']['battery_voltage'].toFixed(2) + " V";
    batteryCurrent.innerHTML = json['live_data']['battery_charge_current'].toFixed(2) + " A";
    batteryPercentage.innerHTML = json['live_data']['battery_percentage'].toFixed(2) + " %"; 

    /* Statistics */
    //houseConsumptionStats.innerHTML = json['statistics']['house_consumption'].toFixed(2) + " kWh";
    //pvProductionStats.innerHTML = json['statistics']['pv_production'].toFixed(2) + " kWh";
    //batteryChargedStats.innerHTML = json['statistics']['battery_charged_energy'].toFixed(2) + " kWh";
    //batteryDischaredStats.innerHTML = json['statistics']['battery_discharged_energy'].toFixed(2) + " kWh";
    //gridExportStats.innerHTML = json['statistics']['grid_export'].toFixed(2) + " kWh";
    //gridImportStats.innerHTML = json['statistics']['grid_import'].toFixed(2) + " kWh";

}

function getRemainingBatteryDuration(json) {
    if ( (-json['live_data']['battery_charge_power']).toFixed(2) > 0.0 ) {
        /* remainingPercentage to 0,xxx times 10 kWh battery capacity */
        return ((json['live_data']['battery_percentage'].toFixed(2) / 100 * json['battery_information']['design_capacity']) / (-json['live_data']['battery_charge_power']).toFixed(2)).toFixed(2) + " h";
    } else {
        return "-";
    }
}

function getIcon(name, size, color="black") {
    let icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    switch(color) {
        case "green":
            icon.setAttribute("class", "bi text-success");
            break;
        case "yellow":
            icon.setAttribute("class", "bi text-warning");
            break;
        case "red":
            icon.setAttribute("class", "bi text-danger");
            break;
        default:
            icon.setAttribute("class", "bi");
    }
    icon.setAttribute("width", size);
    icon.setAttribute("height", size);
    icon.setAttribute("fill", "currentColor");
    let iconUse = document.createElementNS("http://www.w3.org/2000/svg", "use");
    iconUse.setAttribute("href", "/static/senec/icons/bootstrap-icons.svg#" + name);
    icon.appendChild(iconUse);
    return icon;
}

function updateBatteryChargeStateIcon(div, name, size, color="black") {
    if(div.children.length == 0) {
        div.appendChild(getIcon(name, size, color));
    } else {
        div.replaceChild(getIcon(name, size, color), div.firstChild);
    }
}

function replaceElement(elemA, elemB) {
    elemA.parentNode.replaceChild(elemB, elemA);
}
