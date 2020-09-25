window.addEventListener('DOMContentLoaded', function () {
    updateHTML();
    setInterval(() => {
        updateHTML();
    }, 2000);
});

function updateHTML() {
    /*  */
    fetch("/excess?format=json")
        .then(response => {
            return response.json();
        })
        .then(json => {
            updateHelperHTML(json);
        });
}

function updateHelperHTML(json) {
    let excessPower = document.querySelector('#excessPower');

    excessPower.innerHTML = (json['excessPower'] / 1000).toFixed(2) + " kW";
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
    iconUse.setAttribute("href", "/static/pv-excess/icons/bootstrap-icons.svg#" + name);
    icon.appendChild(iconUse);
    return icon;
}

function replaceElement(elemA, elemB) {
    elemA.parentNode.replaceChild(elemB, elemA);
}