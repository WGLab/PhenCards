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
            }
        $(this).DataTable({
                "pageLength": 5,
                "lengthMenu": [[5, 20, 50, -1], [5, 20, 50, "All"]],
                "order": [[ col, sort ]],
                responsive: true,
                columnDefs: [
                    { width: 200, targets: 0 }
                ]
            });
        if(!$(this).parent().hasClass("table-responsive")){
            $(this).wrap("<div class='table-responsive'></div>");
            }
        });
});
