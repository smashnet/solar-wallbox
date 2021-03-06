window.addEventListener('DOMContentLoaded', function () {
    initActions();
    
    updateHTML();
    setInterval(() => {
        updateHTML();
    }, 5000);
});

function initActions() {
    let maxAmpereSelect = document.querySelector('#maxAmpereSelect');
    maxAmpereSelect.addEventListener('change', function () {
        let selected = maxAmpereSelect.options.selectedIndex;
        let maxAmpereValue = maxAmpereSelect.options.item(selected).value;
        fetch("/go-echarger?set=max_ampere=" + maxAmpereValue)
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
        fetch("/go-echarger?set=access_control=" + unlockMethod.value)
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
            fetch("/go-echarger?set=allow_charging=1")
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
            fetch("/go-echarger?set=allow_charging=0")
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
    fetch("/go-echarger?format=json")
        .then(response => {
            return response.json();
        })
        .then(json => {
            updateHelperHTML(json);
        });
}

function updateHelperHTML(json) {
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
    let chargingStatus = document.querySelector('#chargingStatus');
    let chargingPower = document.querySelector('#chargingPower');
    let usedPhases = document.querySelector('#usedPhases');
    let energyCharged = document.querySelector('#energyCharged');

    chargingStatus.innerHTML = json['charging']['status'];
    chargingPower.innerHTML  = json['charging']['current_power'] + " kW";
    usedPhases.innerHTML  = json['charging']['pha_used'];
    energyCharged.innerHTML = json['charging']['energy'] + " kWh";

    // Device Information
    let serialNumber = document.querySelector('#serialNumber');
    let firmwareVersion = document.querySelector('#firmwareVersion');
    let ipAddress = document.querySelector('#ipAddress');

    serialNumber.innerHTML = json['device_serial'];
    firmwareVersion.innerHTML = json['fw_version'];
    ipAddress.innerHTML = json['device_ip'];
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