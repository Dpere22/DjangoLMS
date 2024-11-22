import { $ } from "/static/jquery/src/jquery.js";
function say_hi(elt) {
    console.log("Welcome to", elt.text());
}

say_hi($("h1"));

$( ".sortable" ).on("click", (e) => {
    let header = $(e.target);
    let tbl = header.closest("table");

    tbl.find(".sortable").not(header).removeClass("sort-asc sort-desc").addClass("unsorted").attr("aria-sort", "none");

    if (header.hasClass("unsorted")) {
        header.removeClass("unsorted").addClass("sort-asc").attr("aria-sort", "ascending");
    }
    else if (header.hasClass("sort-desc")) {
        header.removeClass("sort-desc").addClass("unsorted").attr("aria-sort", "none");
    }
    else {
        header.removeClass("sort-asc").addClass("sort-desc").attr("aria-sort", "descending");
    }

    make_table_sortable(header);
});


function make_table_sortable(header){
    console.log("make it here");
    let table = header.closest("table");
    let rows = table.find("tbody tr").toArray();
    let sortableElement = header;
    let columnIndex = sortableElement.index();

    if(sortableElement.hasClass( "unsorted" )){
        rows.sort((rowA, rowB) => {
            let indexA = parseInt($(rowA).attr("data-index"), 10) || 0;
            let indexB = parseInt($(rowB).attr("data-index"), 10) || 0;
            return indexA - indexB;
        })
    }
    else {
        rows.sort((rowA, rowB) => {
            let cellA = $(rowA).children().eq(columnIndex);
            let cellB = $(rowB).children().eq(columnIndex);
            let textA = cellA.text().trim().toLowerCase();
            let textB = cellB.text().trim().toLowerCase();

            let valueA = textA === "missing" ? Number.NEGATIVE_INFINITY
                        : textA === "ungraded" ? Number.MIN_SAFE_INTEGER
                        : parseFloat(cellA.attr("data-value")) || 0;

            let valueB = textB === "missing" ? Number.NEGATIVE_INFINITY
                        : textB === "ungraded" ? Number.MIN_SAFE_INTEGER
                        : parseFloat(cellB.attr("data-value")) || 0;
            if (sortableElement.hasClass("sort-desc")) {
                return valueA - valueB;
            } else {
                return valueB - valueA;
            }
        });
    }
    table.find("tbody").append(rows);
}
