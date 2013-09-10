
/* adapted from networkx js example:
http://networkx.github.io/documentation/latest/examples/javascript/force.html
*/

function ForceGraph(config) {
  /* minimally requires a url to json data, e.g.:
      ForceGraph({url: "/my/data/json"});
      optional can specify width and height
      optionally takes a list of identifiers for nodes to highlight
      Set labels to True for in-graph labels using force-directed layout
      (not recommended for large graphs).

  */

  var options = {
    'width': 400,
    'height': 400,
    'fill': d3.scale.category20(),
    'highlight': [],
    'labels': false,
  };
  $.extend(options, config);

  var vis = d3.select("#chart")
    .append("svg:svg")
      .attr("width", options.width)
      .attr("height", options.height);

  return d3.json(config.url, function(json) {
  var force = d3.layout.force()
      .charge(-1000)
      .linkDistance(120)
      .gravity(0.5)   // 0.1 is the default
      .linkStrength(function(x) { return x.weight || 1; })
      .nodes(json.nodes)
      .links(json.links)
      .size([options.width, options.height])
      .start();

  // force-adjusted labels
  // based on http://bl.ocks.org/MoritzStefaner/1377729
  // OPTIONALLY initialize force-directed labels
  if (options.labels) {
    var label_nodes = [];
    var label_links = [];

    // generate labels based on actual nodes
    for(var i = 0; i < json.nodes.length; i++) {
      // add twice: once to track the node
      label_nodes.push({node: json.nodes[i]});
      // and once to generate a label that will be bound to the node
      label_nodes.push({node: json.nodes[i]});
      // add a link between the node and its label
      label_links.push({
          source : i * 2,
          target : i * 2 + 1,
          weight : 1
      });
    }

    // generate a secondary force-directed graph for the labels
    var force_labels = d3.layout.force()
      .nodes(label_nodes)
      .links(label_links)
      .gravity(0)
      .linkDistance(12)
      .linkStrength(15)
      .charge(-50)
      .size([options.width, options.height])
      .start();

  }

  var link = vis.selectAll("line.link")
      .data(json.links)
    .enter().append("svg:line")
      .attr("class", "link")
//      .style("stroke-width", function(d) { return Math.sqrt(d.value); })
// line width based on weight of the connection
      .style("stroke-width", function(d) { return Math.sqrt(d.weight || 1); })
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  var node = vis.selectAll("g.node")
      .data(json.nodes)
    .enter().append("svg:g")
      .attr("class", function(d) { return "node " + d.type; })
      .style("fill", function(d) { return options.fill(d.type); });

    node.append("svg:circle")
        .attr("r", 5)
// rough-cut at sizing node by degree (ish)
//        .attr("r", function(d) {return 3 * Math.sqrt(d.weight || 1); })
        .style("fill", function(d) { return options.fill(d.type); });

  // when not using force-directed graph labels, add node label
  // for display as hover text
  if (! options.labels) {
    node.append("title")
      .text(function(d) { return d.label; });
  }

    node.call(force.drag);

  if (options.labels) {

    var anchorLink = vis.selectAll("line.anchorLink").data(label_links);

    var anchorNode = vis.selectAll("g.anchorNode")
      .data(force_labels.nodes()).enter()
        .append("svg:g")
        .attr("class", function(d) {
            var cls = "anchorNode";
            if ($.inArray(d.node.id, options.highlight) != -1) {
              cls += " highlight";
            }
            return cls;
          })
        .attr("id", function(d) { return d.node.id; });

    anchorNode.append("svg:circle").attr("r", 0).style("fill", "#FFF");
      anchorNode.append("svg:text").text(function(d, i) {
        return i % 2 === 0 ? "" : d.node.label;
      })
      .attr('class', 'node-label');
      // NOTE: styles configured in css for easier override on hover/highlight

  }

  vis.style("opacity", 1e-6)
    .transition()
      .duration(1000)
      .style("opacity", 1);


      var updateLink = function() {
        this.attr("x1", function(d) {
          return d.source.x;
        }).attr("y1", function(d) {
          return d.source.y;
        }).attr("x2", function(d) {
          return d.target.x;
        }).attr("y2", function(d) {
          return d.target.y;
        });

      };

      var updateNode = function() {
        this.attr("transform", function(d) {
          return "translate(" + d.x + "," + d.y + ")";
        });

      };

  force.on("tick", function() {
    if (options.label) {
      force_labels.start();
    }

    node.call(updateNode);


    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    if (options.labels) {
        anchorNode.each(function(d, i) {
          if (i % 2 === 0) {
            //node: position where the real version of this node is
            d.x = d.node.x;
            d.y = d.node.y;
          } else {

            var b = this.childNodes[1].getBBox();

            var diffX = d.x - d.node.x;
            var diffY = d.y - d.node.y;
            var dist = Math.sqrt(diffX * diffX + diffY * diffY);

            var shiftX = b.width * (diffX - dist) / (dist * 2);
            shiftX = Math.max(-b.width, Math.min(0, shiftX));
            var shiftY = 5;
            this.childNodes[1].setAttribute("transform", "translate(" + shiftX + "," + shiftY + ")");
          }
        });

        anchorNode.call(updateNode);
        link.call(updateLink);
        anchorLink.call(updateLink);

    }

  });
});

}
