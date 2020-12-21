$(document).ready(function () {
    names = ["#hpolink","#cohd","#msh","#doid","#phen2gene","#ohdsi","#open990g","#open990f","#irs990","#hpo","#nihfoa","#icd10","#pharos","#nihreporter"];
    var col;
    var sort;
    $.each(names, function(index, value) {
        switch ($(value).attr('id')) {
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
        var table = $(value).DataTable(mergedDefaults);
        });
});
