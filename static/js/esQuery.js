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
                                    "fuzziness": "AUTO:0,6",
                                },
                                "skip_duplicates": true,
                                "size": 10,
                                "contexts": {
                                    "set": [
                                    {
                                    "context": "HPO",
                                    "boost": 5
                                    },
                                    {
                                    "context": "OHDSI",
                                    "boost": 3
                                    },
                                    {
                                    "context": "MeSH",
                                    "boost": 5
                                    },
                                    {
                                    "context": "DOID",
                                    "boost": 1
                                    },
                                    {
                                    "context": "HPOlink",
                                    "boost": 2
                                    },
                                    {
                                    "context": "ICD-10",
                                    "boost": 4
                                    }
                                    ]
                                }
                            }
                        }
                    },
                    "_source": ["NAME","ID"],
                    "sort": {"_score": {"order": "desc"}}
                };
                

                $.ajax({
                    type: "POST",
                    url: "/autosuggest",
                    async: false,
                    data: JSON.stringify(postData),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (data) {
                        var resultsArray = (data.suggest.name[0].options);
                        for (var i = 0; i < resultsArray.length; i++) {
                            arr.push({
                                'label' : resultsArray[i]['_source']['ID'],
                                'value' : resultsArray[i]['_source']['NAME']
                            });
                        }
                        response(arr);
                    },
                    failure: function (errMsg) {
                        alert(errMsg);
                    }
                });
            },
            focus: function( event, ui ) {
				$( "#typeahead" ).val( ui.item.value );
				return false;
			},
			select: function( event, ui ) {
				$( "#typeahead" ).val( ui.item.value );
				return false;
			},
            minLength: 3, delay: 300
        })
        .data( "ui-autocomplete" )._renderItem = function( ul, item ) {
			return $( "<li></li>" )
				.data( "ui-autocomplete-item", item )
                .append( "<span style='color:grey'>" + item.label + "</span> " + "<span>" + item.value + "</span>")
				.appendTo( ul );
		};
    });


});


