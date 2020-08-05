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
                    },
                    "_source": ["NAME","ID"]
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
				.data( "item.autocomplete", item )
                .append( "<span style='color:grey'>" + item.label + "</span> " + "<span>" + item.value + "</span>")
				.appendTo( ul );
		};
    });


});


