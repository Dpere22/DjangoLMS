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

$('.shouldAsync').ready((event)=> {
    let $forms = $('form.shouldAsync')
    if($forms.length) {
        let form = $(event.target).closest("form");
        make_form_async(form);
    }
});

function make_form_async(jForm){
    $( ".shouldAsync" ).on( "submit", function( event ) {
        let jForm = $(event.target).closest("form");
        event.preventDefault();
        if (!(jForm instanceof jQuery)) {
            console.error('The parameter is not a jQuery-wrapped form.');
            return;
        }
        let formData = new FormData(jForm[0]);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        $.ajax({
            headers: {'X-CSRFToken': csrfToken},
            method: "POST",
            url: jForm.attr("action"),
            data: formData,
            type: "POST",
            processData: false,
            contentType: false,
            mimeType: jForm.attr("enctype"),
            success: () => {
                jForm.replaceWith('<p> Upload succeeded </p>');
            },
            error: () => {
                jForm.find('input, button').prop("disabled", true);
                console.log("Form Submission Failed");
            }
        });
        jForm.find('input, button').prop("disabled", true);
    });
}

$(document).ready((event)=> {
    let $h = $('.hypothesize')
    if($h.length) {
        make_grade_hypothesized($h);
    }
});

function make_grade_hypothesized(jTable){
    console.log("made it to hypothesize");
    if (!(jTable instanceof jQuery)) {
        console.error('The parameter is not a jQuery-wrapped form.');
    }
    let $button = $('<button>')
        .text('Hypothesize') // Set the button's text
        .on('click', function() {
            if (jTable.hasClass("hypothesized")) {
                jTable.removeClass("hypothesized");
                console.log("should change back")
                jTable.find('input').each(function() {
                    const $input = $(this);
                    const originalText = $input.data('original-text');
                    $input.closest('td').text(originalText);
                });
                computeGrade(jTable)
            }
            else{
                console.log("should become inputs")
                jTable.addClass("hypothesized")
                $button.text("Actual Grades")
                jTable.find('td').each(function() {
                    const $td = $(this);
                    const text = $td.text().trim();
                    if (text === 'Ungraded' || text === 'Not Due') {
                        const $input = $('<input>')
                            .data('original-text', text).attr('data-weight', $td.attr('data-weight'));
                        $td.empty().append($input);
                    }
                });
                computeGrade(jTable)
            }

        });

    // Add the button before the table
    jTable.before($button);
}

$(document).ready(function () {
    $(document).on('keyup', 'table.hypothesize input', function () {
        const $table = $(this).closest('table');
        computeGrade($table);
    });
});

function computeGrade(jTable){
    console.log("computing!")
    let totalWeightedGrade = 0;
    let totalWeight = 0;

    jTable.find('tbody tr').each(function() {
        const $row = $(this);
        const $lastElement = $row.find('td:last, input:last'); // Find the last element in the row

        let grade = 0;
        let weight = parseFloat($lastElement.attr('data-weight')) || 0; // Get the weight or default to 0

        if ($lastElement.is('input')) {
            let input = $($lastElement.find('input'));
            let value = input.val();
            grade = parseFloat(value);
        } else if ($lastElement.is('td')) {
            const text = $lastElement.text().trim();
            if (text === 'Missing') {
                grade = 0; // Treat "Missing" as a grade of 0
            } else {
                grade = parseFloat(text); // Try to parse the number
            }
        }

        // Check if the grade is a valid number
        if (!isNaN(grade) && weight > 0) {
            totalWeightedGrade += grade * (weight / 100); // Add the weighted grade
            totalWeight += weight; // Add the weight to the total
        }
    });

    const finalGrade = totalWeight > 0 ? (totalWeightedGrade / (totalWeight / 100)).toFixed(2) : 'N/A';

    // Update the last <td> in the <tfoot> with the final grade
    const $tfootLastTd = jTable.find('tfoot td:last');
    if ($tfootLastTd.length > 0) {
        $tfootLastTd.text(finalGrade + "%");
    } else {
        console.error('No <tfoot> with a last <td> found in the table.');
    }
}
