
/* adapted from networkx js example:
http://networkx.github.io/documentation/latest/examples/javascript/force.html
*/

function ForceGraphControls(config) {
  var options = {
    target: '#graph-controls',
    graph_options: {
      target: '#chart',  // needs a default here so we can remove svg (?)
    }
  };
  $.extend(options, config);

  var controls = $(options.target);
  controls.append($("<h4>Graph Settings</h4>"));

  // checkbox to toggle in-graph labels
  // TODO: perhaps this could default to checked for graphs smaller
  // than a certain threshold. (?)
  var label_toggle = $("<input/>").attr('type', 'checkbox').attr('id', 'graph-labels');
  var p = $("<p>").append(label_toggle).append(" display labels <br/>");
  p.append($("<small>(not recommended for large graphs)</small>"));
  controls.append(p);
  options.graph_options.labels = $("#graph-labels").is(":checked");

  var size_attributes = {
    degree: {label: 'degree', attr: 'degree'},
    in_degree: {label: 'in degree', attr: 'in_degree'},
    out_degree: {label: 'out degree', attr: 'out_degree'},
    betweenness: {label: 'betweenness', attr: 'betweenness'},
    eigenvc: {label: 'eigenvector centrality', attr: 'eigenvector_centrality'},
  };

  // load data so we can inspect to see if we have degree info, find max/min degrees
  d3.json(options.graph_options.url, function(json) {
    options.graph_options.data = json;   // store for re-use when generating actual graph

    var key;
    var initial_range = [3, 20];
    var sizeopts = {};

    for (key in size_attributes) {
      field_opts = size_attributes[key];
      if (json.nodes[0][field_opts.attr] !== undefined) {  // in some cases, could be zero
        sizeopts[key] = {};
        var minmax = [
            d3.min(json.nodes, function(n) { return n[field_opts.attr]; }),
            d3.max(json.nodes, function(n) { return n[field_opts.attr]; })
        ];
        sizeopts[key].min_max = minmax;

        // generate an input to select this feature as basis for size
        sizeopts[key].input = $("<input/>").attr('type', 'radio')
             .attr('name', 'node-size').attr('value', key);
        // TODO: label
        // generate scale for this feature based on observed min/max
        // convert degree or other attribute into relative node size
        sizeopts[key].scale = d3.scale.linear().range(initial_range)
            .domain(minmax);

      }
   } // end for loop through size attribute keys

    // adjust node size
    var p2 = $("<p/>").append("Size nodes by: <br/>");
    // TODO: have an option to switch back to all the same size?
    var none = $("<input/>").attr('type', 'radio').attr('name', 'node-size').attr('value', 'none');

    for (key in sizeopts) {
      p2.append(sizeopts[key].input).append(' ' + size_attributes[key].label + ' ');
    }
    controls.append(p2);
    // slider control for min/max node size
    controls.append($("<input/>").attr('type', 'text')
      .attr('id', 'range').attr('style', 'border: 0; color: #f6931f; font-weight: bold;'));
    controls.append($("<div> </div>").attr('id', 'nodesize-range'));
    $("#nodesize-range").slider({
        range: true,
        min: initial_range[0],  // if any smaller than 3 or so, color becomes invisible
        max: initial_range[1],
        values: [5, 18],
        slide: function(event, ui) {
          $("#range").val(ui.values[0] + " - " + ui.values[1]);
        }
    });
    // display currently selected range
   $("#range").val($("#nodesize-range").slider("values", 0) +
      " - " + $("#nodesize-range").slider("values", 1));

    options.graph_options.nodesize = function nodesize(x) {
      var sizetype = $("input[name=node-size]:checked").val();
      var values = $("#nodesize-range" ).slider("option", "values");

      if (sizeopts[sizetype]) {
        // adjust the scale for this attribute to current slider values
        sizeopts[sizetype].scale.range(values);
        // get the appropriate attribute from the node and scale it
        return sizeopts[sizetype].scale(x[size_attributes[sizetype].attr]);
      }

      return 5;  // default size
    };

  // declare variable to hold the forcedirected graph once it's launched
  var force;

  function launch_graph(options) {
    // destroy previous version of the graph and re-create it with updated options
    d3.select(options.target + " svg").remove();
    force = ForceGraph(options);
    return force;
  }

  // initial launch; store force graph object for later interactions
  force = launch_graph(options.graph_options);

  // if in-graph label option is toggled, update label setting and relaunch the graph
  label_toggle.change(function() {
    options.graph_options.labels = $(this).is(':checked');
    launch_graph(options.graph_options);
  });

  // if degree is selected or slider changes, resume the graph
  // (force node size to be recalculated using existing function)
  for (key in sizeopts) {
    // bind change method for all resize-attribute inputs
    sizeopts[key].input.change(force.resume());
  }
  $("#nodesize-range").slider().on('slidechange', function(event, ui) {
    force.resume();
  });

  });  //end json load
}


function ForceGraph(config) {
  /* minimally requires a url to json data, e.g.:
      ForceGraph({url: "/my/data/json"});
      optional can specify width and height
      optionally takes a list of identifiers for nodes to highlight
      Set labels to True for in-graph labels using force-directed layout
      (not recommended for large graphs).

  */

  var options = {
    'target': '#chart', // selector for element where svg should be added
    'width': 400,
    'height': 400,
    'fill': d3.scale.category20(),
    'highlight': [],
    'labels': false,
    'nodesize': 5,
  };
  $.extend(options, config);

  var vis = d3.select(options.target)
    .append("svg:svg")
      .attr("width", options.width)
      .attr("height", options.height);

function init_graph(json) {

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
        .attr("r", options.nodesize)
        .style("fill", function(d) { return options.fill(d.type); });

    // plain text labels reading left-to-right after the node
    /*
    node.append('svg:text')
        .attr('class', 'node-label')
        .attr('x', 10)  // offset so text doesn't overlap node
        .attr('dy', '.31em')
        .text(function(d) { return ' ' + d.label ;});
    */

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
    if (options.labels) {
      force_labels.start();
    }

    node.call(updateNode);
    // update nodesize based on function/ui controls
    node.selectAll("circle").attr("r", options.nodesize);


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

return force;
}

// if json data is already loaded and passed in, use it
if (options.data) {
  return init_graph(options.data);
} else {
  return d3.json(options.url, init_graph);
  // FIXME: this doesn't actually return the force-directed graph
  // because the json call is asynchronous
}

}
