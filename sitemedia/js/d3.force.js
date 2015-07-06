if (!String.prototype.format) {
  // convenience function for formatting string for svg:path start/end
  String.prototype.format = function() {
    var formatted = this;
    for (var arg in arguments) {
        formatted = formatted.replace("{" + arg + "}", arguments[arg]);
    }
    return formatted;
  };
}

/* adapted from networkx js example:
http://networkx.github.io/documentation/latest/examples/javascript/force.html
*/

function ForceGraphControls(config) {
  var options = {
    target: '#graph-controls',
    graph_options: {
      target: '#chart',  // needs a default here so we can remove svg (?)
      degree_toggles: [],  // list of integer values, e.g. [1, 2]
      width: 'auto',  // FIXME: not getting picked up and must be set in calling code for some reason
    }
  };
  $.extend(options, config);

  // special config for auto width: set graph width based on parent container size
  if (options.graph_options.width == 'auto') {
    options.resize = true;
    options.graph_options.width = parseInt(d3.select(options.graph_options.target).style('width'), 10);
  }

  var controls = $(options.target);

  // one/two-degree toggle if configured
  if (options.graph_options.degree_toggles) {
    var dgr = $("<p>");
    var degree_val;
    for (var i = 0; i < options.graph_options.degree_toggles.length; i++) {
      degree_val = options.graph_options.degree_toggles[i];
      var input = $("<input/>").attr('type', 'radio').attr('name', 'ego-degree')
         .attr('value', degree_val);
         if (i === 0) { input.attr('checked', 'checked'); }
      dgr.append(input);
      dgr.append(" " + degree_val + "-degree ");
    }
    controls.append(dgr);
    var ego_degree = $("input[name='ego-degree']");
    controls.append($('<hr/>'));
  }


  var size_attributes = {
    degree: {label: 'degree', attr: 'degree', default: true},
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

    // slider control for node visibility by size
    var initial_nodesize = initial_range[0];
    var visnodediv = $('<div>display nodes with size >= </div>').attr('id', 'visnodesize-controls');
    visnodediv.append($("<input/>").attr('type', 'text').attr('value', initial_nodesize)
      .attr('id', 'visnode-size').attr('class', 'range-slider'));
    visnodediv.append($("<div> </div>").attr('id', 'visnodesize-range'));

    controls.append(visnodediv);
    $("#visnodesize-range").slider({
        min: initial_range[0],  // if any smaller than 3 or so, color becomes invisible
        max: initial_range[1],
        values: initial_nodesize,
        slide: function(event, ui) {
          $("#visnode-size").val(ui.value);
        }
    });
    controls.append($('<hr/>'));


    // checkbox to toggle in-graph labels
    // TODO: perhaps this could default to checked for graphs smaller
    // than a certain threshold. (?)
    var label_toggle = $("<input/>").attr('type', 'checkbox').attr('id', 'graph-labels');
    var p = $("<p>").append(label_toggle).append(" display labels <br/>");
    // don't show warning if labels are enabled by default
    if ( ! options.graph_options.labels) {
      var labeltip = $("<small>(not recommended for large graphs)</small>").attr('id', 'label-tip');
      p.append(labeltip);
    }
    controls.append(p);
    // if labels is specified as true in user-config, start with it checked
    if (options.graph_options.labels) {
      label_toggle.attr('checked', 'checked');
    }
    options.graph_options.labels = $("#graph-labels").is(":checked");

    // slider control for label visibility by node size
    var initial_labelsize = initial_range[0];
    if (options.graph_options.label_minsize) {
      initial_labelsize = options.graph_options.label_minsize;
    }
    var labelsizediv = $('<div>if node size >= </div>').attr('id', 'vislabelsize-controls');
    // labelsizediv.append("if node size >= ");
    labelsizediv.append($("<input/>").attr('type', 'text').attr('value', initial_labelsize)
      .attr('id', 'vislabel-size').attr('class', 'range-slider'));
    // labelsizediv.append(" or greater");
    labelsizediv.append($("<div> </div>").attr('id', 'vislabelsize-range'));
    if (! options.graph_options.labels) {
      labelsizediv.hide();  // ugh; mixing jquery and d3 control styles throughout
    }
    controls.append(labelsizediv);
    $("#vislabelsize-range").slider({
        min: initial_range[0],  // if any smaller than 3 or so, color becomes invisible
        max: initial_range[1],
        values: initial_labelsize,
        slide: function(event, ui) {
          $("#vislabel-size").val(ui.value);
        }
    });
    controls.append($('<hr/>'));

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
        sizeopts[key].input = $("<input/>").attr({
          type: 'radio', name: 'node-size', value: key, id: key});
        if (size_attributes[key].default) {
          sizeopts[key].input.attr('checked', 'checked');
        }
        // TODO: label
        // generate scale for this feature based on observed min/max
        // convert degree or other attribute into relative node size
        sizeopts[key].scale = d3.scale.linear().range(initial_range)
            .domain(minmax);

      }
   } // end for loop through size attribute keys

    // adjust node size
    var p2 = $("<p/>").append("Size nodes by: <br/>");
    for (key in sizeopts) {
      p2.append($('<label/>').attr('class', 'radio-inline')
        .append(sizeopts[key].input, size_attributes[key].label)
      );
    }
    controls.append(p2);
    // slider control for min/max node size
    controls.append($("<input/>").attr('type', 'text')
      .attr('id', 'range').attr('class', 'range-slider'));
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

    // method to determine if a label should be visible with current settings
    options.graph_options.labels_visible = function(d) {
    if ($("#graph-labels").is(":checked")) {
      if (typeof(d)==='undefined') {
        // generic - are labels enabled or not
        return 'visible';
      } else {
        // specific node: check aginst current user-configured size
        if (options.graph_options.nodesize(d.node) >= $("#vislabel-size").val()) {
          return 'visible';
        } else {
          return 'hidden';
        }
      }
    } else {
      return 'hidden';
    }
  };

    // method to determine if a node should be visible with current settings
    options.graph_options.node_visible = function(d) {
      if (typeof(d) ==='undefined') {
        // generic - are nodes visible or not
        return 'visible';
      } else {
        // specific node: check aginst current user-configured minimum size
        if (options.graph_options.nodesize(d) >= $("#visnode-size").val()) {
          return 'visible';
        } else {
          return 'hidden';
        }
      }
  };

  // method to determine visibility based on two conditions
  options.graph_options.both_visible = function(a, b) {
      // if they match, doesn't matter which one we return; if they don't, one is hidden
      if (a == b) { return a; } else { return 'hidden'; }
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

  if (options.graph_options.degree_toggles) {
    // reload data when 1/2 degree is changed
    ego_degree.change(function() {
       // value of the radio button is the degree to use
       var new_degree = $(this).attr('value');
       var base_url = options.graph_options.url;
      // strip out previous ?degree=N option if any
      if (base_url.indexOf('?') != -1) {
        base_url = base_url.substring(0, base_url.indexOf('?'));
      }
      $.extend(options.graph_options, {
        url: base_url + '?degree=' + new_degree
      });
      // clear out previously loaded data to force loading new json
      delete options.graph_options.data;
      $('.graph-loading').show();   // show loading indicator while graph is re-initialized
      launch_graph(options.graph_options);
    });
  }


  // if in-graph label option is toggled, update label setting and resume the graph
  label_toggle.change(function() {
      force.resume();
      labelsizediv.toggle();  // toggle display of control for labels by size
      $('#label-tip').toggle();
  });

  // function to update visible nodes, links, and label nodes when controls change
  function update_visible_nodes() {
    var node = d3.selectAll("g.node")
        .attr('visibility', function(d) { return options.graph_options.node_visible(d); });
    var label_node = d3.selectAll("g.anchorNode")
        .attr('visibility', function(d) { return options.graph_options.node_visible(d.node); });

    var link = d3.selectAll("path.link")
        .attr('visibility', function(d) {
          // a link should be visible if both source and target nodes are visible
          var src_vis = options.graph_options.node_visible(d.source);
          var tgt_vis = options.graph_options.node_visible(d.target);
          return options.graph_options.both_visible(src_vis, tgt_vis);
        });
    force.resume();
  }

  function resume_update() {
    // resume the graph so any size changes take effect
    force.resume();
    // update node visibility (which could change based on node sizes)
    update_visible_nodes();
  }


  // if degree is selected or slider changes, resume the graph
  // (force node size to be recalculated using existing function)
  for (key in sizeopts) {
    // bind change method for all resize-attribute inputs
    sizeopts[key].input.on('change', function(event, ui) {
      resume_update();
    });
  }
  $("#nodesize-range").slider().on('slidechange', function(event, ui) {
    resume_update();
  });

  $("#visnodesize-range").slider().on('slidechange', function(event, ui) {
    resume_update();
  });

  // method to resize svg & force graph based on parent container
  function resize() {
    var width = parseInt(d3.select(options.graph_options.target).style('width'), 10);
    var dims = force.size();
    // reset width of force-directed graph (used to calculate center of graph)
    force.size([width, dims[1]]);  // preserve current height
    force.resume();   // resume in case graph has stabilized, so it will redraw
    $('svg').width(width);
  }

  // when using auto width, resize svg & force graph on window resize
  if (options.resize) {
    d3.select(window).on('resize', resize);
  }

  });  //end json load
}


function ForceGraph(config) {
  /* minimally requires a url to json data, e.g.:
      ForceGraph({url: "/my/data/json"});
      optional can specify width and height
      optionally takes a list of identifiers for nodes to highlight
      Set labels to True for in-graph labels using force-directed layout
      (not recommended for large graphs).

    Available options:

      target: jquery selector for element where svg chart should be added
      url: url for json data to be used for the graph
      width: width of the svg element which will contain the graph
      height: height of the svg element
      highlight: list of node ids to be highlighted (labeled, bold)
      labels: true/false; should force-directed labels be displayed
      node_info_url: url for displaying node information; will be called
        with node id as param, e.g. url?id=nodeid

  */

  var options = {
    target: '#chart', // selector for element where svg should be added
    width: 400,
    height: 400,
    highlight: [],
    labels: false,
    nodesize: 5,
    curved_paths: false,
    gravity: 1,
    link_distance: 100,
    link_weight_adjustment: 1,
    charge: -1000,
    node_info: '#node-info',
    node_info_url: ''
  };
  $.extend(options, config);

  function node_info(id) {
    $(options.node_info).html('Loading...').load(options.node_info_url + "?id=" + id);
  }
  if (! options.node_info_url) {
    $(options.node_info).hide();
  }
  // calculate width based on parent container
  var width = parseInt(d3.select(options.target).style('width'), 10);

  var vis = d3.select(options.target)
    .append("svg:svg")
      .attr("width", options.width)
      .attr("height", options.height);


function init_graph(json) {

  var force = d3.layout.force()
      .charge(options.charge)
      .linkDistance(options.link_distance)
      .gravity(options.gravity)   // 0.1 is the default
      .linkStrength(function(x) { return x.weight || 1; })
      .nodes(json.nodes)
      .links(json.links)
      .size([options.width, options.height])
      .start();

  $('.graph-loading').hide();   // hide loading indicator once graph is initialized

  // "sticky" behavior on drag/double-click from http://bl.ocks.org/mbostock/3750558
  function dblclick(d) {
    d3.select(this).classed("fixed", d.fixed = false);
  }

  function dragstart(d) {
    d3.select(this).classed("fixed", d.fixed = true);
  }

  var drag = force.drag()
    .on("dragstart", dragstart);

  // force-adjusted labels
  // based on http://bl.ocks.org/MoritzStefaner/1377729
  // OPTIONALLY initialize force-directed labels
  var label_nodes = [];
  var label_links = [];
  var force_labels;
  // if (options.labels) {
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
    force_labels = d3.layout.force()
      .nodes(label_nodes)
      .links(label_links)
      .gravity(0)
      .linkDistance(12)
      .linkStrength(15)
      .charge(-50)
      .size([options.width, options.height])
      .start();

  // } end if labels

  var path = vis.selectAll("path")
      .data(json.links)
      .enter().append("svg:path")
      .attr("class", "link")
      // line width based on weight of the connection
      .style("stroke-width", function(d) { return Math.sqrt(d.weight || 1) * options.link_weight_adjustment; })
      .attr('source', function(d) { return d.source.id; })
      .attr('target', function(d) { return d.target.id; })
      .attr("d", function(d) {
        return "M {0},{1} L {2},{3}".format(d.source.x, d.source.y,
          d.target.x, d.target.y);
      });

  var node = vis.selectAll("g.node")
      .data(json.nodes)
    .enter().append("svg:g")
      .attr("class", function(d) { return "node " + d.type; })
      .on("dblclick", dblclick)
      .call(drag);

    if (options.node_info_url) {
      node.classed('node-info-link', true);
    }

    node.append("svg:circle")
        .attr("r", options.nodesize);

    // click for node info IF defined
    if (options.node_info_url) {
      node.on("click", function(d) { node_info(d.id); });
    }

    // highlight corresponding label on mouseover
    function highlight_label(node, on_off) {
        // find anchor node that corresponds to this one
        var labels = d3.selectAll('g.anchorNode').filter(function(j, i) {
           return j.node.id == node.id;
        });
        labels.classed('hover', on_off);
    }
    if (options.labels) {
      node.on("mouseover", function(d) { highlight_label(d, true); });
      node.on("mouseout", function(d) { highlight_label(d, false); });
    }

    // plain text labels reading left-to-right after the node
    /*
    node.append('svg:text')
        .attr('class', 'node-label')
        .attr('x', 10)  // offset so text doesn't overlap node
        .attr('dy', '.31em')
        .text(function(d) { return ' ' + d.label ;});
    */

  // add node label for display as hover text
  // (needs to be always present since force-directed labels will always
  // be added but may not all be visible)
  node.append("title")
    .text(function(d) { return d.label; });

  node.call(force.drag);

    var anchorLink = vis.selectAll("line.anchorLink").data(label_links);

    var anchorNode = vis.selectAll(".anchorNode")
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

    anchorNode.append("svg:circle").attr("r", 0);
      anchorNode.append("svg:text").text(function(d, i) {
        return i % 2 === 0 ? "" : d.node.label;
      })
      .attr('class', 'node-label')
      .attr('visibility', function(d) {
          return options.both_visible(options.labels_visible(d),
                             options.node_visible(d.node));
      });

      if (options.node_info_url) {
        anchorNode.classed('node-info-link', true);
      }
      // NOTE: styles configured in css for easier override on hover/highlight

      if (options.node_info_url) {
        anchorNode.on("click", function(d) {
            node_info(d.node.id);
        });
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

      var updatePath = function() {
        this.attr("d", function(d) {
          return "M {0},{1} L {2},{3}".format(d.source.x, d.source.y,
            d.target.x, d.target.y);
        });
      };
      // logic for curved paths borrowed from http://bl.ocks.org/mbostock/1153292
      function linkArc(d) {
        var dx = d.target.x - d.source.x,
        dy = d.target.y - d.source.y,
        dr = Math.sqrt(dx * dx + dy * dy);
        return "M{0},{1} A{2},{3} 0 0,1 {4},{5}".format(
          d.source.x, d.source.y, dr, dr, d.target.x, d.target.y);
      }

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

    // update label visibility
    anchorNode.selectAll('.node-label')
       .attr('visibility', function(d) {
          return options.both_visible(options.labels_visible(d),
                             options.node_visible(d.node));
        });

      // NOTE: would be nice if we could skip this if labels aren't visible
      // (slow for large graphs), but in some cases that results in the
      // label graph getting disconnected from the main graph
        anchorNode.each(function(d, i) {
          if (i % 2 === 0) {
            // node: position where the real version of this node is
            d.x = d.node.x;
            d.y = d.node.y;
          } else {
            var childNode = this.childNodes[1];
            bounds = childNode.getBoundingClientRect();
            // Workaround for Firefox with getBBox on non-rendered svg elements;
            // - if node isn't currently visible or rendered, skip it.
            if (bounds.height === 0 && bounds.width === 0) {
              return;
            }
            var b = childNode.getBBox();

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
        anchorLink.call(updateLink);

    // }

    if (options.curved_paths) {
      path.attr("d", linkArc);
    } else {
      path.call(updatePath);
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
