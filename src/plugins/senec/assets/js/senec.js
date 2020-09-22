window.addEventListener('DOMContentLoaded', function () {
    setInterval(() => {
        updateHTML()
    }, 2000);
});

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
    let housePower = document.querySelector('#housePower');
    let batteryCharge = document.querySelector('#batteryCharge');
    let gridPull = document.querySelector('#gridPull');
    let inverterPower = document.querySelector('#inverterPower');
    let batteryDischarge = document.querySelector('#batteryDischarge');
    let gridPush = document.querySelector('#gridPush');
    let batteryChargeState = document.querySelector('#batteryChargeState');
    let batteryRemainingTime = document.querySelector('#batteryRemainingTime');
    let batteryChargeStateIcon = document.querySelector('#batteryChargeStateIcon');

    housePower.innerHTML = (json['housePower'] / 1000).toFixed(2) + " kW";
    if(json['batteryChargeRate'] > 0) {
        /* Battery charging */
        batteryCharge.innerHTML = (json['batteryChargeRate'] / 1000).toFixed(2) + " kW";
        batteryDischarge.innerHTML = "0.00 kW";

        if(json['batteryPercentage'].toFixed(2) < 20.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "red");
        } else if (json['batteryPercentage'].toFixed(2) < 50.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "yellow");
        } else if (json['batteryPercentage'].toFixed(2) <= 100.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "green");
        }
    } else {
        /* Battery discharging */
        batteryDischarge.innerHTML = (json['batteryDischargeRate'] / 1000).toFixed(2) + " kW";
        batteryCharge.innerHTML = "0.00 kW";

        batteryRemainingTime.innerHTML = getRemainingBatteryDuration(json);
        if(json['batteryPercentage'].toFixed(2) < 20.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery", 32, "red");
        } else if (json['batteryPercentage'].toFixed(2) < 50.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-half", 32, "yellow");
        } else if (json['batteryPercentage'].toFixed(2) <= 100.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-full", 32, "green");
        }
    }
    if(json['gridPull'] > 0) {
        gridPull.innerHTML = (json['gridPull'] / 1000).toFixed(2) + " kW";
        gridPush.innerHTML = "0.00 kW";
    } else {
        gridPush.innerHTML = (json['gridPush'] / 1000).toFixed(2) + " kW";
        gridPull.innerHTML = "0.00 kW";
    }
    inverterPower.innerHTML = (json['PVProduction'] / 1000).toFixed(2) + " kW";
    batteryChargeState.innerHTML = json['batteryPercentage'].toFixed(2) + " %";
    
}

function getRemainingBatteryDuration(json) {
    if ( (json['batteryDischargeRate'] / 1000).toFixed(2) > 0.0 ) {
        /* remainingPercentage to 0,xxx times 10 kWh battery capacity */
        return ((json['batteryPercentage'].toFixed(2) / 100 * json['batteryCapacity']) / (json['batteryDischargeRate'] / 1000).toFixed(2)).toFixed(2) + " Stunden";
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