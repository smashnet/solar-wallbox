let batteryChargeState, batteryChargeStateIcon;
let housePower, pvProduction, gridPower, batteryPower,
    wallbox1, wallbox1_switch, wallbox2, wallbox2_switch;
let automaticCharging_switch;

window.addEventListener('DOMContentLoaded', function () {
    initVars();
    updateHTML();
    setInterval(() => {
        updateHTML();
    }, 2000);
});

function initVars() {
    batteryChargeState = document.querySelector('#batteryChargeState');
    batteryChargeStateIcon = document.querySelector('#batteryChargeStateIcon');

    pvProduction = document.querySelector('#pvProduction');
    gridPower = document.querySelector('#gridPower');
    batteryPower = document.querySelector('#batteryPower');

    housePower = document.querySelector('#housePower');
    wallbox1 = document.querySelector('#wallbox1');
    wallbox1_switch = document.querySelector('#wallbox1_switch');
    wallbox2 = document.querySelector('#wallbox2');
    wallbox2_switch = document.querySelector('#wallbox2_switch');

    automaticCharging_switch = document.querySelector('#automaticCharging_switch');

    wallbox1_switch.addEventListener('change', function () {
        if(this.checked) {
            fetch("/go-echarger?device=0&set=allow_charging=1")
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        this.checked = false;
                        console.log(json['error']);
                    }
                });
        } else {
            fetch("/go-echarger?device=0&set=allow_charging=0")
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        this.checked = true;
                        console.log(json['error']);
                    }
                });
        }
    });

    wallbox2_switch.addEventListener('change', function () {
        if(this.checked) {
            fetch("/go-echarger?device=1&set=allow_charging=1")
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        this.checked = false;
                        console.log(json['error']);
                    }
                });
        } else {
            fetch("/go-echarger?device=1&set=allow_charging=0")
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        this.checked = true;
                        console.log(json['error']);
                    }
                });
        }
    });

    automaticCharging_switch.addEventListener('change', function () {
        if(this.checked) {
            fetch("/dashboard?setAutomaticCharging=1")
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        this.checked = false;
                        console.log(json['error']);
                    }
                });
        } else {
            fetch("/dashboard?setAutomaticCharging=0")
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        this.checked = true;
                        console.log(json['error']);
                    }
                });
        }
    });
}

function updateHTML() {
    /*  */
    fetch("/dashboard?format=json")
        .then(response => {
            return response.json();
        })
        .then(json => {
            updateHelperHTML(json);
        });
}

function updateHelperHTML(json) {
    /* Production and Storage */
    pvProduction.innerHTML = json['house']['live_data']['pv_production'].toFixed(2) + " W";
    gridPower.innerHTML = json['house']['live_data']['grid_power'].toFixed(2) + " W";
    batteryPower.innerHTML = json['house']['live_data']['battery_charge_power'].toFixed(2) + " W";

    if(json['house']['live_data']['battery_charge_power'] > 0) {
        /* Battery charging */
        if(json['house']['live_data']['battery_percentage'].toFixed(2) < 20.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "red");
        } else if (json['house']['live_data']['battery_percentage'].toFixed(2) < 50.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "yellow");
        } else if (json['house']['live_data']['battery_percentage'].toFixed(2) <= 100.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-charging", 32, "green");
        }
    } else {
        /* Battery discharging */
        if(json['house']['live_data']['battery_percentage'].toFixed(2) < 20.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery", 32, "red");
        } else if (json['house']['live_data']['battery_percentage'].toFixed(2) < 50.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-half", 32, "yellow");
        } else if (json['house']['live_data']['battery_percentage'].toFixed(2) <= 100.0) {
            updateBatteryChargeStateIcon(batteryChargeStateIcon, "battery-full", 32, "green");
        }
    }
    batteryChargeState.innerHTML = json['house']['live_data']['battery_percentage'].toFixed(2) + " %";

    /* Consumers */
    let houseConsumption = json['house']['live_data']['house_power'] - json['wallbox1']['charging']['current_power'] - json['wallbox2']['charging']['current_power'];
    housePower.innerHTML = houseConsumption.toFixed(2) + " W";
    wallbox1.innerHTML  = json['wallbox1']['charging']['current_power'] + " W";
    wallbox1_switch.checked = json['wallbox1']['access_control']['allow_charging'];
    wallbox2.innerHTML  = json['wallbox2']['charging']['current_power'] + " W";
    wallbox2_switch.checked = json['wallbox2']['access_control']['allow_charging'];

    automaticCharging_switch.checked = json['automaticCharging']
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