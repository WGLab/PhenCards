function removeNonAsc(s) {
	s = s.replace(/[^\x00-\x7F]/g, "");
	return s;
}

function normalizeSpace(s) {
	s = s.replace(/ +(?= )/g, '');
	s = s.replace(/\n\s*\n/g, '\n');
	return s;
}

function textLimitCheck(s){
	if(s.length > 10000){
		alert('WARNING: System might be CRASHED if the length of the documents > 10,000 !. Try to submit seperately');
	}
}

function formatText(s) {
	s = removeNonAsc(s);
	s = normalizeSpace(s);
	return s;
}

function highlight(note, parsingJson) {
	note = formatText(note);
	$("#parsingResults").text(note);
	$("#parsingResults").addClass('entities');
	var context = document.querySelector("#parsingResults");

	// using https://markjs.io/
        var options = {}
	var instance = new Mark(context);
	for ( var key in parsingJson) {
		subObj = _.pick(parsingJson[key], [ 'start', 'length' ]);
                if (parsingJson[key]['negated']){
                    neg = "negated";
                }
                else {
                    neg = "term";
                }
	        options = {
		"element" : "mark",
		"className" : neg,
		"exclude" : [],
		"iframes" : true,
		"iframesTimeout" : 5000,
		"each" : function(node, range) {
			// node is the marked DOM element
			// range is the corresponding range
			// processEachTag(node, range, parsingJson);
		},
		"filter" : function(textNode, range, term, counter) {
			// textNode is the text node which contains the found term
			// range is the found range
			// term is the extracted term from the matching range
			// counter is a counter indicating the number of marks for the found
			// term
			return true; // must return either true or false
		},
		"noMatch" : function(range) {
			// the not found range
		},
		"done" : function(counter) {
			// counter is a counter indicating the total number of all marks
		},
		"debug" : false,
		"log" : window.console
            }
	    instance.markRanges([subObj], options);
	};
	// instance.mark('Individual');
}
