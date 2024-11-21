import { $ } from "/static/jquery/src/jquery.js";
function say_hi(elt) {
    console.log("Welcome to", elt.text());
}

say_hi($("h1"));

$( ".sortable" ).on("click", (e) => {
    let header = $(e.target);
    if(header.hasClass("unsorted") || header.hasClass("sort-desc")) {
        header.removeClass( "unsorted sort-desc" ).addClass( "sort-asc" );
    }
    else{
        header.removeClass( "sort-asc" ).addClass( "sort-desc" );
    }
    let tbl = header.closest("table");
    make_table_sortable(tbl);
});

function make_table_sortable(tbl){
    console.log("make it here");
    let rows = tbl.find("tbody tr").toArray();
    let sortableElement = $(tbl.find(".sortable"));

    rows.sort((rowA, rowB) => {
        let textA = $(rowA).find("td:last").text().trim().toLowerCase();
        let textB = $(rowB).find("td:last").text().trim().toLowerCase();

        // Convert text to values for comparison
        let valueA = textA === "missing" ? Number.NEGATIVE_INFINITY
                    : textA === "ungraded" ? Number.MIN_SAFE_INTEGER
                    : parseFloat(textA) || 0;
        let valueB = textB === "missing" ? Number.NEGATIVE_INFINITY
                    : textB === "ungraded" ? Number.MIN_SAFE_INTEGER
                    : parseFloat(textB) || 0;
        if(sortableElement.hasClass( "sort-desc" )) {
            return valueA - valueB;
        }
        else{
            return valueB - valueA;
        }
    });

    tbl.find("tbody").append(rows);
}
