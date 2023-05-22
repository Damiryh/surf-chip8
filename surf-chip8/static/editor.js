function getData() {
    return {
        "name": $('input[name="name"]')[0].value,
        "source": $('textarea[name="source"]')[0].value
    };
}

function saveSnippet(id) {
    if (id === undefined) {
        saveSnippetAs();
        return;
    }
    
    let xhr = new XMLHttpRequest();
    xhr.open('PUT', `/snippets/${id}`, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.send(JSON.stringify(getData()));
    xhr.onload = function () {
        let message = JSON.parse(xhr.responseText).message;
        $('.toast-header span')[0].innerText = "Save";
        $('.toast-body')[0].innerText = message;
        $('.toast').toast('show');
    };
}

function saveSnippetAs() {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', `/snippets/new`, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.send(JSON.stringify(getData()));
    xhr.onload = function () {
        let message = JSON.parse(xhr.responseText).message;
        $('.toast-header span')[0].innerText = "Save As";
        $('.toast-body')[0].innerText = message;
        $('.toast').toast('show');
    };
}

createNewSnippet = saveSnippetAs

function deleteSnippet(id) {
    let xhr = new XMLHttpRequest();
    xhr.open('DELETE', `/snippets/${id}`, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.send(JSON.stringify('{}'));
    xhr.onload = function () {
        let message = JSON.parse(xhr.responseText).message;
        $('.toast-header span')[0].innerText = "Delete";
        $('.toast-body')[0].innerText = message;
        $('.toast').toast('show');
    };
}
