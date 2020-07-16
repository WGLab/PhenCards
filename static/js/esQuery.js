//Ready function when page is loaded
$(document).ready(function () {
    //Autocomplete function
    $(function () {
        $("#typeahead").autocomplete({
            source: function (request, response) {
                var arr = new Array();
                var postData = {
                    "suggest": {
                        "name": {
                            "text": request.term.toLowerCase(),
                            "completion": {
                                "field": "NAMESUGGEST",
                                "fuzzy": {
                                    "fuzziness": 1
                                },
                                "skip_duplicates": true,
                                "size": 10
                            }
                        }
                    }
                };

                $.ajax({
                    type: "POST",
                    url: "http://localhost:9200/autosuggest/_search",
                    async: false,
                    data: JSON.stringify(postData),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (data) {
                        var resultsArray = (data.suggest.name[0].options);
                        for (var i = 0; i < resultsArray.length; i++) {
                            arr.push(resultsArray[i].text);
                        }
                        response(arr);
                    },
                    failure: function (errMsg) {
                        alert(errMsg);
                    }
                });
            },
            minLength: 3, delay: 300
        })
    });


});


