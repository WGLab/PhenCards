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
        var mergedDefaults = {...tableDefault, ...{"order":order}}
        var table = $(this).DataTable(mergedDefaults);
                
    });
});
