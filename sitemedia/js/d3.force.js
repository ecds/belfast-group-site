
/* adapted from networkx js example:
http://networkx.github.io/documentation/latest/examples/javascript/force.html
*/

function ForceGraph(config) {
  /* minimally requires a url to json data, e.g.:
      ForceGraph({url: "/my/data/json"});
      optional can specify width and height
  */

  var options = {
    'width': 400,
    'height': 400,
    'fill': d3.scale.category20()
  };
  $.extend(options, config);
  console.log(options);

  var vis = d3.select("#chart")
    .append("svg:svg")
      .attr("width", options.width)
      .attr("height", options.height);

  return d3.json(config.url, function(json) {
  var force = d3.layout.force()
      .charge(-120)
      .linkDistance(80)
      .gravity(0.1)
      .linkStrength(function(x) { return x.weight || 1; })
      .nodes(json.nodes)
      .links(json.links)
      .size([options.width, options.height])
      .start();

  var link = vis.selectAll("line.link")
      .data(json.links)
    .enter().append("svg:line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return Math.sqrt(d.value); })
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  var node = vis.selectAll("circle.node")
      .data(json.nodes)
    .enter().append("svg:circle")
      .attr("class", function(d) { return "node " + d.type; })
      .attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; })
      .attr("r", 5)
      .style("fill", function(d) { return options.fill(d.type); })
      .call(force.drag);

  node.append("svg:title")
      .text(function(d) { return d.label; });

  vis.style("opacity", 1e-6)
    .transition()
      .duration(1000)
      .style("opacity", 1);

  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  });
});

}
