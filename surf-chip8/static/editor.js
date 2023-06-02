function toast(header, message) {
    $('.toast-header span')[0].textContent = header;
    $('.toast-body')[0].textContent = message;
    $('.toast').toast('show');
}

function getData() {
    return {
        "name": $('input[name="name"]')[0].value,
        "source": $('textarea[name="source"]')[0].value
    }
};

$('button#save-as').bind('click', function() {
    fetch('/snippets/new', {
        "method": "POST",
        "headers": { "Content-Type": "application/json" },
        "body": JSON.stringify(getData())
    })
    .then( response => response.json() )
    .then( response => {
        toast("Save as", response.message);
        if (response.new_id === undefined) return;
        setTimeout(() => location.assign(`/snippets/${response.new_id}`), 2000);
    });
});

$('button#save').bind('click', function() {
    if (!$SNIPPET_ID) {
        $('button#save-as').click();
        return;
    }
    
    fetch(`/snippets/${$SNIPPET_ID}`, {
        "method": "PUT",
        "headers": { "Content-Type": "application/json" },
        "body": JSON.stringify(getData())
    })
    .then( response => response.json() )
    .then( response => toast("Save", response.message) );
});

$('button#delete').bind('click', function() {
    if (!confirm("Delete this snippet?")) return;
    
    fetch(`/snippets/${$SNIPPET_ID}`, {
        "method": "DELETE",
        "headers": { "Content-Type": "application/json" },
        "body": "{}"
    })
    .then( response => response.json() )
    .then( response => {
        toast("Delete", response.message);
        setTimeout(() => location.assign('/'), 2000);
    });
});

$('button#assemble').bind('click', function() {    
    fetch(`/snippets/${$SNIPPET_ID}/assemble?binary=0`)
    .then( response => response.json() )
    .then( response => {
        toast("Assemble", response.message);
    });
});


$('button#run').bind('click', function() {    
    location.assign(`/snippets/${$SNIPPET_ID}/run`);
});

function getLineAndColumn(textarea){
    var textLines = textarea.value.substr(0, textarea.selectionStart).split("\n");
    var currentLine = textLines.length;
    var currentColumn = textLines[textLines.length-1].length;
    $('#location')[0].innerText = `${textarea.selectionStart}:${currentLine}:${currentColumn+1}`;
}
