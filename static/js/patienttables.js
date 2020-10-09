$(document).ready(function () {
    var col;
    var sort;
    $('table').each(function() {
        switch ($(this).attr('id')) {
            case "patient_terms":
            case "phen2gene":
                col = 1;
                sort = "asc";
                break;
            case "linked_diseases":
                col = 1;
                sort = "desc";
                break;
            }
            if (col && sort) {
                order = [[col, sort]];
            }
            else {
                order = [];
            }
        $(this).DataTable({
                "pageLength": 5,
                "lengthMenu": [[5, 20, 50, -1], [5, 20, 50, "All"]],
                "order": order,
                responsive: true
            });
        });
});
