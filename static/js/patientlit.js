// using select2, creates removable blocks that one can literature search with
// this can potentially be used for HPO terms in disease search
// https://scholar.google.com/scholar?hl=en&q="intellectual+disability"+OR+"cortical+atrophy"+OR+"flat+nasal+bridge"+OR+"loss+of+bladder+control"+OR+"smooth+philtrum"+OR+"synophrys"+OR+"thick+lips"+OR+"unibrow"+OR+"ventricular+dilatation"+
function searchQuery() {
    var lquery = "";
    var x = document.getElementsByClassName("tag label label-info")
    var i;
    lquery = "";
    for (i = 0; i < x.length; i++) {
        y = x[i].innerText;
        if (y != "OR" && y != "AND") {
            lquery = lquery + '"' + y + '"' + "+";
            }
        else {
            lquery = lquery + y + "+";
        }
    }
    console.log(lquery);
    return lquery;
};
function searchResult() {
    window.open("https://scholar.google.com/scholar?hl=en&q="+searchQuery(), "_blank")
}
