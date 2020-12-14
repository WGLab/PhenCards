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
            case "nihfoa":
                col = 7;
                sort = "desc";
                break;
            case "icd10":
                col = 3; 
                sort = "desc";
                break;
            case "pharos":
            case "d2e":
            case "nihreporter":
                col = "";
                sort = "";
                break;
            }
            if (col && sort) {
                order = [[col, sort]];
            }
            else {
                order = [];
            }
        var mergedDefaults = {...tableDefault, ...{"order": order, "columnDefs": [{ "width": "25%", "targets": 0 }]}}
        var table = $(this).DataTable(mergedDefaults);
        });
});
