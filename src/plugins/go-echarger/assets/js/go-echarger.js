window.addEventListener('DOMContentLoaded', function () {
    initActions();
    
    updateHTML();
    setInterval(() => {
        updateHTML();
    }, 2000);
});

let baseurl = "/go-echarger";

function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

function getUrlParam(parameter, defaultvalue){
    var urlparameter = defaultvalue;
    if(window.location.href.indexOf(parameter) > -1){
        urlparameter = getUrlVars()[parameter];
        }
    return urlparameter;
}

function initActions() {
    // Enhance baseurl with used device
    baseurl = baseurl + "?device=" + getUrlParam('device', '0')
    let maxAmpereSelect = document.querySelector('#maxAmpereSelect');
    maxAmpereSelect.addEventListener('change', function () {
        let selected = maxAmpereSelect.options.selectedIndex;
        let maxAmpereValue = maxAmpereSelect.options.item(selected).value;
        fetch(baseurl + "&set=max_ampere=" + maxAmpereValue)
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        console.log(json['error']);
                    }else if(json['msg'] == "success!") {
                        let main = document.querySelector('main');
                        main.insertBefore(createAlert("Successfully set max ampere to " + maxAmpereValue, "success"), main.firstChild);
                    }
                });
    });

    let unlockMethodSelect = document.querySelector('#unlockMethodSelect');
    unlockMethodSelect.addEventListener('change', function () {
        let selected = unlockMethodSelect.options.selectedIndex;
        let unlockMethod = unlockMethodSelect.options.item(selected);
        fetch(baseurl + "&set=access_control=" + unlockMethod.value)
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        console.log(json['error']);
                    }else if(json['msg'] == "success!") {
                        let main = document.querySelector('main');
                        main.insertBefore(createAlert("Successfully set access method to " + unlockMethod.innerHTML, "success"), main.firstChild);
                    }
                });
    });

    let allowChargingToggle = document.querySelector('#allowChargingToggle');
    allowChargingToggle.addEventListener('change', function () {
        if(this.checked) {
            fetch(baseurl + "&set=allow_charging=1")
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
            fetch(baseurl + "&set=allow_charging=0")
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
    fetch(baseurl + "&format=json")
        .then(response => {
            return response.json();
        })
        .then(json => {
            updateHelperHTML(json);
        });
}

function updateHelperHTML(json) {

    let chargingStatus = document.querySelector('#chargingStatus');
    chargingStatus.innerHTML = json['charging']['status'];

    // Access Controls
    let allowChargingToggle = document.querySelector('#allowChargingToggle');
    let unlockMethodSelect = document.querySelector('#unlockMethodSelect');
    let unlockedByUser = document.querySelector('#unlockedByUser');
    let userEnergy = document.querySelector('#userEnergy');

    allowChargingToggle.checked = json['access_control']['allow_charging'];
    unlockMethodSelect.options.selectedIndex = getSelectedIndex(unlockMethodSelect, json['access_control']['access_method']);
    let userID = json['access_control']['unlocked_by'];
    if(userID > 0) {
        unlockedByUser.innerHTML = json['access_control']['rfid_cards'][userID]['name'];
        userEnergy.innerHTML = json['access_control']['rfid_cards'][userID]['energy']/10.0 + " kWh";
    }else {
        unlockedByUser.innerHTML = "None";
        userEnergy.innerHTML = "- kWh";
    }
    

    // Power Settings
    let maxAmpereSelect = document.querySelector('#maxAmpereSelect');
    
    maxAmpereSelect.options.selectedIndex = getSelectedIndex(maxAmpereSelect, json['charging']['max_ampere']);

    // Current Charging Process
    let chargingPower = document.querySelector('#chargingPower');
    let usedPhases = document.querySelector('#usedPhases');
    let energyCharged = document.querySelector('#energyCharged');
    let totalEnergyCharged = document.querySelector('#totalEnergyCharged');

    chargingPower.innerHTML  = json['charging']['current_power'] + " kW";
    usedPhases.innerHTML  = json['charging']['pha_used'];
    energyCharged.innerHTML = json['charging']['energy'] + " kWh";
    totalEnergyCharged.innerHTML = json['energy_total']/10.0 + " kWh";

    // Device Information
    let serialNumber = document.querySelector('#serialNumber');
    let firmwareVersion = document.querySelector('#firmwareVersion');
    let ipAddress = document.querySelector('#ipAddress');
    let errorStatus = document.querySelector('#errorStatus');

    serialNumber.innerHTML = json['device_serial'];
    firmwareVersion.innerHTML = json['fw_version'];
    ipAddress.innerHTML = json['device_ip'];
    errorStatus.innerHTML = json['error_state'];
}

function getSelectedIndex(select, value) {
    for(i = 0; i < select.options.length; i++) {
        if(value == select.options.item(i).value) {
            return i;
        }
    }
}

function createAlert(text, type="success") {
    let alert = document.createElement("div");
    alert.setAttribute("id", "alert");
    switch(type) {
        case "success":
            alert.setAttribute("class", "alert alert-success alert-dismissible fade show");
            break;
        case "warning":
            alert.setAttribute("class", "alert alert-warning alert-dismissible fade show");
            break;
        case "error":
            alert.setAttribute("class", "alert alert-danger alert-dismissible fade show");
            break;
        default:
            alert.setAttribute("class", "alert alert-secondary alert-dismissible fade show");
    }
    alert.setAttribute("role", "alert");
    alert.innerHTML = text;

    // dismiss button
    let button = document.createElement("button");
    button.setAttribute("type", "button");
    button.setAttribute("class", "btn-close");
    button.setAttribute("data-dismiss", "alert");
    button.setAttribute("aria-label", "Close");

    // add to alert
    alert.appendChild(button);

    return alert;
}

function replaceElement(elemA, elemB) {
    elemA.parentNode.replaceChild(elemB, elemA);
}