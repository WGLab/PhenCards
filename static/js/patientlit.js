// using select2, creates removable blocks that one can literature search with
// this can potentially be used for HPO terms in disease search
// https://scholar.google.com/scholar?hl=en&q="intellectual+disability"+OR+"cortical+atrophy"+OR+"flat+nasal+bridge"+OR+"loss+of+bladder+control"+OR+"smooth+philtrum"+OR+"synophrys"+OR+"thick+lips"+OR+"unibrow"+OR+"ventricular+dilatation"+
$(".js-example-tags").select2({
  tags: true
});
var lquery = "";
function searchQuery() {
    var x = document.getElementById("select2-hposelect-container").getElementsByTagName("li");
    var i;
    lquery = "";
    for (i = 0; i < x.length-1; i++) {
        if (x[i].title != "OR" && x[i].title != "AND") {
            lquery = lquery + '"' + x[i].title + '"' + "+";
            }
        else {
            lquery = lquery + x[i].title + "+";
        }
    }
    lquery = lquery + '"' + x[i].title + '"';
};
$(document).ready(function() {
    searchQuery();
});
$("#hposelect").on("select2:close", function (e) {
    searchQuery();
});
function searchResult() {
    window.open("https://scholar.google.com/scholar?hl=en&q="+lquery, "_blank")
}
