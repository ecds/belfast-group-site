function ChordDiagram(config) {
  /* minimally requires two urls to json data, e.g.:
      ChordDiagram({matrix: "adjacency-matrix.json", nodes: "node-data.json"});
      optionally can specify width and height

      - matrix must be an adjacency matrix
      - nodes should include information about nodes in the network,
        in the same order as they are presented in the matrix
        (used for labels and node type)
  */

  var options = {
    target: '#chart',
    'max_size': 720,
    'fill': d3.scale.category20c(),  // was using category20 before...
    // NOTE: assigning separate color by id for now,
    // but if dataset is large enough should probably be by category
    'highlight': [],
  };
  $.extend(options, config);

  // special config for auto width/height: base on parent container size
  var width = d3.min([options.max_size, parseInt(d3.select(options.target).style('width'), 10)]);
  console.log('width = ' + width);
  options.width = options.height = width;

var outerRadius = Math.min(options.width, options.height) / 2 - 10,
    innerRadius = outerRadius - 24;

var formatPercent = d3.format(".1%");

var arc = d3.svg.arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius);

var layout = d3.layout.chord()
    .padding(0.04)
    .sortSubgroups(d3.descending)
    .sortChords(d3.ascending);

var path = d3.svg.chord()
    .radius(innerRadius);

var svg = d3.select(options.target).append("svg")
    .attr("width", options.width)
    .attr("height", options.height)
  .append("g")
    .attr("id", "circle")
    .attr("transform", "translate(" + options.width / 2 + "," + options.height / 2 + ")");

svg.append("circle")
    .attr("r", outerRadius);

return d3.json(config.nodes, function(data) {
    d3.json(config.matrix, function(matrix) {

    // Compute the chord layout.
    layout.matrix(matrix);

    // Add a group per neighborhood.
    var group = svg.selectAll(".group")
        .data(layout.groups)
      .enter().append("g")
        .attr("class", "group")
        .on("mouseover", mouseover)
        .on("mouseout", mouseout);

    // Add a mouseover title.
    group.append("title").text(function(d, i) {
        return data.nodes[i].label;
    });

    // Add the group arc.
    var groupPath = group.append("path")
        .attr("id", function(d, i) { return "group" + i; })
        .attr("d", arc)
    .style("fill", function(d, i) { return options.fill(data.nodes[i].id); });  // or use node.type

    // Add a text label.
    var groupText = group.append("text")
        .attr("x", 6)
        .attr("dy", 15);

    groupText.append("textPath")
        .attr("xlink:href", function(d, i) { return "#group" + i; })
        .text(function(d, i) { return data.nodes[i].label; });

    // Remove the labels that don't fit. :(
        // TODO: add labels orthogonal to the circle, as in other circular diagrams?
    groupText.filter(function(d, i) { return groupPath[0][i].getTotalLength() / 2 - 16 < this.getComputedTextLength(); })
        .remove();

    // Add the chords.
    var chord = svg.selectAll(".chord")
        .data(layout.chords)
      .enter().append("path")
        .attr("class", "chord")
        .style("fill", function(d, i) { return options.fill(data.nodes[d.source.index].id); })  // or node.type
        .attr("d", path);

    function mouseover(d, i) {
      chord.classed("fade", function(p) {
        return p.source.index != i && p.target.index != i;
      });
    }
    // chord example doesn't need this for some reason... (?)
    function mouseout(d, i) {
      chord.classed("fade", false);
    }

   $('.graph-loading').hide();   // hide loading indicator once graph is initialized
  });  // matrix data
}); // node info


}

