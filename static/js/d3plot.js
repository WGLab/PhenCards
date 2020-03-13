$(function(){

var valueLabelWidth = 40; // space reserved for value labels (right)
var barHeight = 12; // height of one bar
var barLabelWidth = 100; // space reserved for bar labels
var barLabelPadding = 5; // padding between bar and bar labels (left)
var gridLabelHeight = 18; // space reserved for gridline labels
var gridChartOffset = 3; // space between start of grid and first bar
var maxBarWidth = 1000; // width of the bar with the max value
$("div").css({'padding':'20px 20px'});
$("a").css({'margin-left':'30px'});
function type(d) {
	  d.value = parseFloat(d.value); // coerce to number
	  return d;
	}
$.ajax({
    url:'out.annotated_gene_list',
    type:'HEAD',
    error: function()
    {
        //file not exists
    	generate_barplot("out.final_gene_list");
    	
    },
    success: function()
    {
        //file exists
    	generate_barplot("out.annotated_gene_list");
    }
});

var generate_barplot = function(file)
{
d3.tsv(file, type, function(error, data) {
	var slice_length;
	if(data.length>=500) slice_length =500;
	else slice_length = data.length;
	data=data.slice(0, slice_length);
	
// accessor functions 
var barLabel = function(d) { return d['Gene']; };
var barValue = function(d) { return parseFloat(d['Score']); };
var colorScale = d3.scale.linear().domain([0,d3.max(data,barValue)]).range(["#ef7788","#5555ef"]);
var colorScale2 = d3.scale.linear().domain([0,d3.max(data,barValue)]).range(["#cf0022","#1111cf"]);
// scales
var yScale = d3.scale.ordinal().domain(d3.range(0, data.length)).rangeBands([0, data.length * barHeight]);
var y = function(d, i) { return yScale(i); };
var yText = function(d, i) { return y(d, i) + yScale.rangeBand() / 2; };
var x = d3.scale.linear().domain([0, d3.max(data, barValue)]).range([0, maxBarWidth]);
// svg container element
var chart = d3.select('#chart').append("svg")
  .attr('width', maxBarWidth + barLabelWidth + valueLabelWidth)
  .attr('height', gridLabelHeight + gridChartOffset + data.length * barHeight);
// grid line labels
var gridContainer = chart.append('g')
  .attr('transform', 'translate(' + barLabelWidth + ',' + gridLabelHeight + ')'); 
gridContainer.selectAll("text").data(x.ticks(10)).enter().append("text")
  .attr("x", x)
  .attr("dy", -3)
  .attr("text-anchor", "middle")
  .text(String);
// vertical grid lines
gridContainer.selectAll("line").data(x.ticks(10)).enter().append("line")
  .attr("x1", x)
  .attr("x2", x)
  .attr("y1", 0)
  .attr("y2", yScale.rangeExtent()[1] + gridChartOffset)
  .style("stroke", "#ccc");
// bar labels
var labelsContainer = chart.append('g')
  .attr('transform', 'translate(' + (barLabelWidth - barLabelPadding) + ',' + (gridLabelHeight + gridChartOffset) + ')'); 
labelsContainer.selectAll('text').data(data).enter().append('text')
  .attr('y', yText)
  .attr('stroke', 'none')
  .attr("font-weight","bold")
  .attr("font-size","15px")
  .attr("dy", ".35em") // vertical-align: middle
  .attr('text-anchor', 'end')
  .append("a").attr("xlink:href", function(d) { return "http://www.ncbi.nlm.nih.gov/gene/" +d.ID; } )
  .attr('target','_blank')
  .attr('opacity','0.8')
  .attr('fill', function(d) { return colorScale2(barValue(d)); })
  .on('mouseover',function(d) { d3.select(this).attr('opacity','1').attr('fill','#fe3333') })
  .on('mouseout',function(d) { d3.select(this).attr('opacity','0.8').attr('fill',function(d) { return colorScale2(barValue(d)); })  })
  .text(barLabel);
// bars
var url = document.URL;
url = url.replace(/barplot.html.*/,""); 
var barsContainer = chart.append('g')
  .attr('transform', 'translate(' + barLabelWidth + ',' + (gridLabelHeight + gridChartOffset) + ')'); 
barsContainer.selectAll("rect").data(data).enter()
  .append("a").attr("xlink:href", function(d,i){ if(i<50) return url+"index.html#"+ d.Rank; })
  .attr('target','_blank')
  .append("rect")
  .on('mouseover',function(d,i) {if(i<50) d3.select(this).attr('fill','#fe3333') })
  .on('mouseout',function(d,i) { if(i<50) d3.select(this).attr('fill',function(d) { return colorScale(barValue(d)); })  })
  .attr('y', y)
  .attr('height', yScale.rangeBand())
  .attr('width', function(d) { return x(barValue(d)); })
  .attr('stroke', 'white')
  .attr('fill', function(d) {return colorScale(barValue(d)); } );
// bar value labels
barsContainer.selectAll("text").data(data).enter().append("text")
  .attr("x", function(d) { return x(barValue(d)); })
  .attr("y", yText)
  .attr("dx", 3) // padding-left
  .attr("dy", ".35em") // vertical-align: middle
  .attr("text-anchor", "start") // text-align: right
  .attr("fill", "#cc3377")
  .attr("font-size","10px")
  .attr("stroke", "none")
  .text(function(d) { return d3.round(barValue(d), 3); });
// start line
barsContainer.append("line")
  .attr("y1", -gridChartOffset)
  .attr("y2", yScale.rangeExtent()[1] + gridChartOffset)
  .style("stroke", "#000");
});         }
});
