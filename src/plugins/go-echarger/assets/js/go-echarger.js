window.addEventListener('DOMContentLoaded', function () {
    initActions();
    
    updateHTML();
    setInterval(() => {
        updateHTML();
    }, 5000);
});

function initActions() {
    let saveMaxAmpereButton = document.querySelector('#saveMaxAmpereButton');
    saveMaxAmpereButton.addEventListener('click', function () {
        let maxAmpereInput = document.querySelector('#maxAmpereInput');
        fetch("/go-echarger?set=max_ampere=" + maxAmpereInput.value)
                .then(response => {
                    return response.json();
                })
                .then(json => {
                    if(json['error']) {
                        this.checked = false;
                        console.log(json['error']);
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
    let chargingStatus = document.querySelector('#chargingStatus');
    let chargingPower = document.querySelector('#chargingPower');
    let usedPhases = document.querySelector('#usedPhases');
    let energyCharged = document.querySelector('#energyCharged');

    let allowChargingToggle = document.querySelector('#allowChargingToggle');
    let maxAmpereInput = document.querySelector('#maxAmpereInput');

    chargingStatus.innerHTML = json['charging']['status'];
    chargingPower.innerHTML  = json['charging']['current_power'] + " kW";
    usedPhases.innerHTML  = json['charging']['pha_used'];
    energyCharged.innerHTML = json['charging']['energy'] + " kWh";

    allowChargingToggle.checked = json['charging']['allow_charging'];
    maxAmpereInput.value = json['charging']['max_ampere'];
}