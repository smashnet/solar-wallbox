window.addEventListener('DOMContentLoaded', function () {
    /*setInterval(() => {
        updateHTML()
    }, 2000);*/
});

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
}