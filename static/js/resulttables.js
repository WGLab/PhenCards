$(document).ready(function () {
    var col;
    var sort;
    $('table').each(function() {
        switch ($(this).attr('id')) {
            case "hpolink":
                col = 5;
                sort = "desc";
                break;
            case "cohd":
            case "msh":
            case "doid":
                col = 2;
                sort = "desc";
                break;
            case "phen2gene":
                col = 1;
                sort = "asc";
                break;
            case "ohdsi":
            case "open990g":
                col = 6;
                sort = "desc";
                break;
            case "open990f":
            case "irs990":
                col = 4;
                sort = "desc";
                break;
            case "hpo":
                col = 6;
                sort = "desc";
                break;
            case "icd10":
                col = 3; 
                sort = "desc";
                break;
            }
        $(this).DataTable({
                "pageLength": 5,
                "lengthMenu": [[5, 20, 50, -1], [5, 20, 50, "All"]],
                "order": [[ col, sort ]],
                "responsive": "true"
            });
        });
});
