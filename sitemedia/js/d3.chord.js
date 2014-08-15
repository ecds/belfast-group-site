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
    //'fill': d3.scale.category20c(),  // was using category20 before...
    'fill': d3.scale.ordinal().range(
      [
      "#8477E5","#978ED8","#9ACCDF","#ACA5E4",
      "#B3DBEB","#C2BBEE","#FFA23C","#FFBB72",
      "#3DB5E3","#614EE8","#69BFE0","#81BAD0",
      "#FFCF9A","#FFD53C","#FFA23C","#FFE172",
      "#FFE1C0","#FFE99A","#FFEEAD","#FFF2C0"]),
    // NOTE: assigning separate color by id for now,
    // but if dataset is large enough should probably be by category
    'highlight': [],
    'node_info_url':''
  };
  $.extend(options, config);

  // special config for auto width/height: base on parent container size
  var width = d3.min([options.max_size, parseInt(d3.select(options.target).style('width'), 10)]);
  console.log('width = ' + width);
  options.width = options.height = width;
  var rd = 200

var outerRadius = Math.min(options.width-rd, options.height-rd) / 2 - 10,
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

    // Returns an event handler for fading a given chord group.
    function fade(opacity) {
      return function(d, i) {
        svg.selectAll("path.chord")
            .filter(function(d) { return d.source.index != i && d.target.index != i; })
          .transition()
            .style("stroke-opacity", opacity)
            .style("fill-opacity", opacity);
      };
    }

    // Add the chords first, so they will be underneath the labels.
    var chord = svg.selectAll(".chord")
        .data(layout.chords)
      .enter().append("path")
        .attr("class", "chord")
        .style({"fill": function(d, i) { return options.fill(data.nodes[d.source.index].id); }})  // or node.type
        .attr("d", path);


    // Add a group per neighborhood.
    var group = svg.selectAll(".group")
        .data(layout.groups)
        .enter().append("g")
        .attr("class", "group")
        .on("mouseover", fade(.04))
        .on("mouseout", fade(.80))

    // Add a mouseover title.
    group.append("title").text(function(d, i) {
        return data.nodes[i].label;
    });

    group.append("id").text(function(d, i) {
        return data.nodes[i].id;
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

    groupText
        .attr("class", function(d, i) { return "chord-label label" + i; })
        .attr("xlink:href", function(d, i) { return "#group" + i; })
        .text(function(d, i) { return data.nodes[i].label; })
        .attr('fill','#000000')
        .attr({'stroke':'#CCC','stroke-width':'0.5px','stroke-linecap':'butt','stroke-linejoin':'miter','stroke-opacity':'0.5'})
        .each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
        .attr("dy", ".35em")
        .attr("text-anchor", function(d) {
          return d.angle > Math.PI ? "end" : null;
        })
        .attr("transform", function(d) {
          var w = outerRadius*2-this.getComputedTextLength(),
              h = outerRadius*2- this.getComputedTextLength(),
              p = 40,
              r0 = Math.min(w, h) * 0.41,
              r1 = r0 * 1.1;
          return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
              + "translate(" + (r0 + this.getComputedTextLength()/3+66) + ")"
              + (d.angle > Math.PI ? "rotate(180)" : "");
        });

    // Remove the labels that don't fit. :(
      console.log($(window).width())
      if($(window).width()<768){
        groupText.remove();
      }

      $("#circle").on('click','g',function(){
        $this = $(this)
        text_node = $this.find('text');
        id_node = $this.find('id');
        var id ='http://localhost:8001/people/ciaran-carson/';
        $('#key').html($("<div/>").addClass('panel').html("<h4 class='text-muted'>"+text_node.text()+"...</h4>").load(options.node_info_url + "?id=" + id_node.text()));
      })

    
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

