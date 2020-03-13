$(window).load(function() {    
	
	
	$('[data-toggle="tooltip"]').tooltip();
	$('.selectpicker').selectpicker({
        width:'100%',
   });      
     $('.selectpicker').selectpicker('refresh');
     $("[data-toggle='popover']").popover({container: 'body',
    	 trigger: 'click',
	   	 html:true
   	  });
     $('#addon_seed').selectpicker('val',['DB_DISGENET_GENE_DISEASE_SCORE', 'DB_GAD_GENE_DISEASE_SCORE', 'DB_GENECARDS_GENE_DISEASE_SCORE']);
     $('#addon_seed').selectpicker('refresh');
     $('#gene_score').selectpicker('selectAll');
//}); 


//$(function(){
	  
	  
	          
                  var gene_selection=   $("#gene_selection");
	              var region_selection= $("#region_selection");
	              var weight_adjust =   $("#weigh_adjust");
                  var gene_options=     $("#gene_selection_options");
                  var region_options=   $("#region_selection_options");
                  var weight_options =  $("#weight_adjust_options");
                  var weight_adjust =   $("#weight_adjust");
                  var wordcloud_options=$("#wordcloud");
                  
                  var input_form=       $("fieldset.input_form");
                  var submit=           $("input[name='submit']");
	              var disease_input =   $("#disease");
	              var email_input   =   $("#email");
	              var other_options =   $("#other_options");
	             
	              var disease_label =   $("label.disease");
	              var gene_selection_label =   $("label.gene_selection_options");
	              var region_selection_label = $("label.region_selection_options");
	              var advanced_options_label = $("label.advanced_options");
	              var wordcloud_label = $("label.wordcloud");
	              var weight_label =    $("label.weight_adjust_options");
	              var title         =   $("h2.gene_prioritization");
	              
	              var submit_div     =  $("div#submit");
	              var orig_color = weight_label.css("color");
	              var msg;
	              disease_label.css("cursor","pointer");
	              gene_selection_label.css("cursor","pointer");
	              region_selection_label.css("cursor","pointer");
	              weight_label.css("cursor","pointer");
	              wordcloud_label.css("cursor","pointer");
	              gene_selection.hide();
	              region_selection.hide();
	              weight_adjust.hide();
	              weight_options.val("no");
	              region_options.val("no");
	              gene_options.val("no");
	            //predefined functions
	              function GeneChange()
	              {
	                    if(gene_options.find("option:selected").val()=="yes") 
	                    {
	                      gene_selection_label.css("color","#d0228f");
                          gene_selection.fadeIn(500);
	                    }
	                     else 
	                    {
	                    	 gene_selection_label.css("color",orig_color);
	                    	 gene_selection.fadeOut(300);
		                }
	              };
	              function RegionChange()
	              {
	 	                if(region_options.find("option:selected").val()=="yes")
	 	                {
	 	                  region_selection_label.css("color","#d0228f");	
	 	                  region_selection.fadeIn(500);
	                    }	 		            
	 	                else 
	 		            {
	 	                	region_selection_label.css("color",orig_color);
	 	                	region_selection.fadeOut(300);
	 		            }
	              };
	             
	              function WeightChange()
	              {
	            	   
	 	                if(weight_options.find("option:selected").val()=="yes")
	 	                {
	 	                  weight_label.css("color","#d0228f");	
	 	                  weight_adjust.fadeIn(500);
	                    }	 		            
	 	                else 
	 		            {
	 	                	weight_label.css("color",orig_color);
	 	                	weight_adjust.fadeOut(300);
	 		            }
	              };
	              function AdvancedChange()
                  {
                       if(other_options.find("option:selected").val()=="all_diseases")
                       {
                      	 msg = disease_input.val();
                           disease_input.prop("disabled","true");
                           disease_input.removeAttr("required");                             
                           disease_input.val("");
                           disease_label.html("All Diseases");
                       }
                       else
                       {  
                      	   disease_input.removeAttr("disabled");
                           disease_input.prop("required","true");
                           if(msg){disease_input.val(msg);}
                           if(other_options.find("option:selected").val()=="phenotype_interpretation")
                           {
                         	disease_label.html("Diseases/Phenotypes");
                           }
                           else if(other_options.find("option:selected").val()=="none")
                           {
                           disease_label.html("Disease Terms");
                           }
                       }	 
                       
                  };
	             $.fn.disableSelection = function() {
	            	        return this
	            	        .attr('unselectable','on')
	            	        .css({'-moz-user-select':'-moz-none',
	            	              '-moz-user-select':'none',
	            	              '-o-user-select':'none',
	            	              '-khtml-user-select':'none', /* you could also put this in a class */
	            	              '-webkit-user-select':'none',/* and add the CSS class here instead */
	            	              '-ms-user-select':'none',
	            	              'user-select':'none'
	            	        })
	            	        .bind('selectstart', function(){ return false; });
	            	    };
	            //turn the text selection off for all labeles
	             $("label").each(function(){
	            	  $(this).replaceWith($(this).disableSelection());
                    });
	              
		          gene_options.change(GeneChange);
	              region_options.change(RegionChange);	
	              weight_options.change(WeightChange);
                  other_options.change(AdvancedChange);
                 
                  var Wordcloud_change =  function(){
              		if($("#wordcloud").selectpicker("val")=="yes"  )
            		{	  
            		  wordcloud_label.css("color","#d0228f");       	 		
            		}
            		else
            		{      		  
            		  wordcloud_label.css("color",orig_color);
            		 
            		}
                }
                  
                  //The label click events
              
                  wordcloud_label.click(function(){
                	  if($("#wordcloud").selectpicker("val")=="yes"  )
              		{
              		  $("#wordcloud").selectpicker("val","no");	  
              		}
              		else
              		{
              		  $("#wordcloud").selectpicker("val","yes");  		 
              		}
                	  Wordcloud_change();
                    });  
                  wordcloud_options.change(Wordcloud_change);  
                    disease_label.click(
                    function(){
                       if(disease_label.html()=="Disease Terms")
                       {	   
                    	   other_options.selectpicker('val', 'all_diseases'); 
                            AdvancedChange();
                       }
                       else if(disease_label.html()=="Diseases/Phenotypes")
                       {                  	   
                    	   other_options.selectpicker('val', 'none'); 
                           AdvancedChange();
                       }
                       
                       else if(disease_label.html()=="All Diseases")
                       {
                    	   other_options.selectpicker('val', 'phenotype_interpretation'); 
                           AdvancedChange();
                       }
                       
                     });		
                    gene_selection_label.click(
                    function(){
                       if(gene_options.find("option:selected").val()=="no")
                    	   {
                    	   gene_options.selectpicker('val', 'yes');                  	  
                    	   }
                       else
                    	   {
                           gene_options.selectpicker('val', 'no');                   	     
                    	   }
                           GeneChange();
  	                    });
                   region_selection_label.click(
                   function(){
                	   if(region_options.find("option:selected").val()=="no")
                	   {
                		   region_options.selectpicker('val', 'yes');                     	  
                	   }
                   else
                	   {
                	   region_options.selectpicker('val', 'no');                        	     
                	   }
                       RegionChange();
                   });
                   weight_label.click(
                           function(){
                              if(weight_options.find("option:selected").val()=="no")
                           	   {
                               weight_options.selectpicker('val', 'yes');                 	  
                           	   }
                              else
                           	   {                         	  
                               weight_options.selectpicker('val', 'no');                    	     
                           	   }
                                  WeightChange();
         	                    });
                      
                    
                   
                   //The instruction function
                  /* title.hover(
                   function(){introduction.eq(0).fadeIn("3000")},
                   function(){introduction.eq(0).fadeOut("3000")}
                  );  */
                   
                 //The autocomplete 
                   
                   var disease_count;
                   var old_string;
                   
                     $.when(
                     $.get('./hot_disease_term.txt', function (data) {
                    	   disease_count = data.split("\n");  
                    	   disease_count.pop();
                	   })
                       ).then(function(){
                       disease_input.autocomplete({ 
                	   source: function( request, response ) {  
                	   var terms = request.term.split(/\s*[^' ,_\.\w\-\[\]\(\)\{\}\/]+\s*/);
                	   var term = terms[terms.length-1];
                	   if(terms.length>=2) {old_string = terms.splice(0,terms.length-1).join("\n");
                	                        old_string += "\n"; }
                	   else {old_string ="";}
                       var matcher = new RegExp( "^" + $.ui.autocomplete.escapeRegex( term ), "i" );
                       var list = $.grep(disease_count , function( item ){return matcher.test( item );} );
                       if(list.length>=50){ list=list.slice(list.length-50);}
                       list = list.reverse();
                       response(list);                                    
                	   },
                	   minLength:0,
                	   position: { my : "left bottom", at: "left top" },
                	   select: function( event, ui ) { 
                		   event.preventDefault();
                		   disease_input.val ( old_string + ui.item.value ); }
                     });
                   });
                 
                         
                  //tooltips
var instruction = "<li>Enter your <b>query terms</b></li>" +
		          "<li>Recommended deliminators <br><b>',' ';' '|' 'Tab' 'Enter'</b>" +
		          "<li>like <b>'alzheimer;dementia' 'cognitive;dysfunction'<br>'fatigue;headache;breath'</b></li>"+
	              "<li>Scores added up for multiple terms</li>"+
			      "<li>Scores higher for intersection genes</li>";
                  disease_input.tooltip({ content: instruction,
                	  position: { my: "left center", at: "right+8 center"},
                	  tooltipClass: "disease_input"});
                  
    instruction = "<b>Click me</b>";
                  disease_label.tooltip({ content: instruction,
                	  position: { my: "right bottom", at: "right top-10"},
                	  tooltipClass: "label_click"});
                  gene_selection_label.tooltip({ content: instruction,
                	  position: { my: "right bottom", at: "right top-10"},
                	  tooltipClass: "label_click"});
                  region_selection_label.tooltip({ content: instruction,
                	  position: { my: "right bottom", at: "right top-10"},
                	  tooltipClass: "label_click"});
                  weight_label.tooltip({ content: instruction,
                	  position: { my: "right bottom", at: "right top-10"},
                	  tooltipClass: "label_click"});
                  wordcloud_label.tooltip({ content: instruction,
                	  position: { my: "right bottom", at: "right top-10"},
                	  tooltipClass: "label_click"});
                  
                  
    instruction = "<li><b>Phenotype interpretation</b>: <br>Interpret phenotype terms into disease names</li>" +
    			  "<li><b>Disease Only:</b> <br>Terms are treated only as disease terms</li>" + 
		          "<li><b>All diseases</b>: <br>Terms neglected, all diseases in database used</li>";
                  advanced_options_label.tooltip({ content: instruction,
                	  position: { my: "right bottom", at: "right top-5"},
                	  tooltipClass: "advanced_instruction"});
    instruction ="<li><b>Optional</b> <br> We will send you an email to inform you when your query has been done";
                 email_input.tooltip({ content: instruction,
  	             position: { my: "left center", at: "right+8 center"},
  	             tooltipClass: "disease_input"});
      instruction ="<li>Gene prioritization could help you get a list of genes with scores assigned. </li>" +
      		       "<li>The score is an indicator of the relations between the gene and your disease term input. </li>" +
      		       "<li>Several authorized gene disease databases are used.</li></h3>";
                  title.tooltip({ content: instruction,
                  position: { my: "center bottom", at: "center top+5"},
                  tooltipClass: "title-tooltip"});

                  var GWAS = $( "#GWAS" ).spinner({ max: 1, min:0, step:0.05 });
                  //GWAS.filter(".ui-spinner-input").prop('disabled', 'true');
                  var OMIM = $( "#OMIM" ).spinner({ max: 1, min:0, step:0.05 });
                  //OMIM.filter(".ui-spinner-input").prop('disabled', 'true');
                  var CLINVAR = $( "#CLINVAR" ).spinner({ max: 1, min:0, step:0.05 });
                  //CLINVAR.filter(".ui-spinner-input").prop('disabled', 'true');
                  var ORPHANET = $( "#ORPHANET" ).spinner({ max: 1, min:0, step:0.05 });
                  //ORPHANET.filter(".ui-spinner-input").prop('disabled', 'true');
                  var GENE_REVIEWS = $( "#GENE_REVIEWS" ).spinner({ max: 1, min:0, step:0.05 });
                  //GENE_REVIEWS.prop('disabled', 'true')
                  var HPRD = $( "#HPRD" ).spinner({ max: 1, min:0, step:0.01 });
                  //HPRD.prop('disabled', 'true')
                  var BIOSYSTEM = $( "#BIOSYSTEM" ).spinner({ max: 1, min:0, step:0.01 });
                  //BIOSYSTEM.prop('disabled', 'true')
                  var HGNC= $( "#HGNC" ).spinner({ max: 1, min:0, step:0.01 });
                  //HGNC.prop('disabled', 'true')
                  var HTRI = $( "#HTRI" ).spinner({ max: 1, min:0, step:0.01 });
                 // HTRI.prop('disabled', 'true')
                  
              

});
//Translate

$(document).on('click','#translate',function(e){
	var text = $('#disease').val();
	$.ajax({
		method: 'POST',
		url:  '/php/translate.php',
		dataType: 'json', 
		accepts: 'json',
		data: {text: text},
		complete: function(data){
			if(data){
				//console.dir(data);
				$('#disease').val(data.responseJSON['translation']);
			}
		}
	});
	return true;
});


//file upload
$(document).on('change', '.btn-file :file', function() {
  var input = $(this),
      numFiles = input.get(0).files ? input.get(0).files.length : 1,
      label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
  input.trigger('fileselect', [numFiles, label]);
});

$(document).ready( function() {

    $('.btn-file :file').on('fileselect', function(event, numFiles, label) {
        
        var input = $(this).parents('.input-group').find(':text'),
            log = numFiles > 1 ? numFiles + ' files selected' : label;
        
        if( input.length ) {
            input.val(log);
        } else {
            if( log ) alert(log);
        }       
        });     
});
                    
                    
  	               
