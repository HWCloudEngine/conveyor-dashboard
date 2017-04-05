/**
 * Adapted for Conveyor js topology generator.
 * Based on:
 * HeatTop JS Framework
 * Dependencies: jQuery 1.7.1 or later, d3 v3 or later
 * Date: June 2013
 * Description: JS Framework that subclasses the D3 Force Directed Graph library to create
 * Heat-specific objects and relationships with the purpose of displaying
 * Stacks, Resources, and related Properties in a Resource Topology Graph.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

var conveyor_container = "#conveyor_plan_topology";

var diagonal = d3.svg.diagonal()
    .projection(function(d) { return [d.y, d.x]; });

function update(){
  node = node.data(nodes, function(d) { return d.id; });
  link = link.data(links);

  var nodeEnter = node.enter().append("g")
    .attr("class", "node")
    .attr("node_name", function(d) { return d.name; })
    .attr("node_id", function(d) { return d.id; })
    .attr("node_type", function(d) { return d.type; })
    .call(force.drag);



  nodeEnter.append("image")
    .attr("xlink:href", function(d) { return d.image; })
    .attr("id", function(d){ return "image_"+ d.id; })
    .attr("x", function(d) { return d.image_x; })
    .attr("y", function(d) { return d.image_y; })
    .attr("width", function(d) { return d.image_size; })
    .attr("height", function(d) { return d.image_size; })
    .attr("clip-path","url(#clipCircle)");
  node.exit().remove();

  link.enter().insert("path", "g.node")
    .attr("class", function(d) { return "link " + d.link_type; });

  link.exit().remove();
  //Setup click action for all nodes
  node.on("mouseover", function(d) {
    $("#info_box").html(d.info_box);
    current_info = d.name;
  });
  node.on("mouseout", function(d) {
    $("#info_box").html('');
  });

  force.start();
}

function tick() {
  link.attr('d', drawLink).style('stroke-width', 3).attr('marker-end', "url(#end)");
  node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
}

function drawLink(d) {
  return "M" + d.source.x + "," + d.source.y + "L" + d.target.x + "," + d.target.y;
}


function set_in_progress(stack, nodes) {
  if (stack.in_progress === true) { in_progress = true; }
  for (var i = 0; i < nodes.length; i++) {
    var d = nodes[i];
    if (d.in_progress === true){ in_progress = true; return false; }
  }
}

function findNode(id) {
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].id === id){ return nodes[i]; }
  }
}

function findNodeIndex(id) {
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].id=== id){ return i; }
  }
}

function addNode (node) {
  nodes.push(node);
  needs_update = true;
  for(var idx=0;idx<nodes.length;idx++){
  }
}

function remove_links(id) {
  var i = 0;
  var n = findNode(id);
  while (i < links.length) {
    if (links[i].source === n || links[i].target === n) {
      links.splice(i, 1);
    } else {
      i++;
    }
  }
  needs_update = true;
}

function removeNode (id) {
  var i = 0;
  var n = findNode(id);
  while (i < links.length) {
    if (links[i].source === n || links[i].target === n) {
      links.splice(i, 1);
    } else {
      i++;
    }
  }
  nodes.splice(findNodeIndex(id),1);
  needs_update = true;
}

function remove_nodes(old_nodes, new_nodes){
  var needed_remove_ids = [];
  //Check for removed nodes
  for (var i=0;i<old_nodes.length;i++) {
    var remove_node = true;
    for (var j=0;j<new_nodes.length;j++) {
      if (old_nodes[i].id === new_nodes[j].id){
        remove_node = false;
        break;
      }
    }
    if (remove_node === true){
      needed_remove_ids.push(old_nodes[i].id);
      //removeNode(old_nodes[i].id);
    }
  }
  for(var index in needed_remove_ids){
    removeNode(needed_remove_ids[index]);
  }
}

function build_link(node) {
    build_node_links(node);
    build_reverse_links(node);
}


function build_links(){
  for (var i=0;i<nodes.length;i++){
    build_node_links(nodes[i]);
    build_reverse_links(nodes[i]);
  }
}

//build_node_links
function build_node_links(node){
  for (var j=0;j<node.required_by.length;j++){
    var push_link = true;
    var target_idx = '';
    var source_idx = findNodeIndex(node.id);
    //make sure target node exists
    try {
      target_idx = findNodeIndex(node.required_by[j]);
    } catch(err) {
      console.log(err);
      push_link =false;
    }
    //check for duplicates
    for (var lidx=0;lidx<links.length;lidx++) {
      if (links[lidx].source === source_idx && links[lidx].target === target_idx) {
        push_link=false;
        break;
      }
    }
    if (push_link === true && (source_idx && target_idx)){
      links.push({
        'target':target_idx,
        'source':source_idx,
        'value':1,
        'link_type': node.link_type
      });
    }
  }
}

//build_reverse_links
function build_reverse_links(node){
  for (var i=0;i<nodes.length;i++){
    if(nodes[i].required_by){
      for (var j=0;j<nodes[i].required_by.length;j++){
        var dependency = nodes[i].required_by[j];
        //if new node is required by existing node, push new link
        if(node.id === dependency){
          links.push({
            'target':findNodeIndex(node.id),
            'source':findNodeIndex(nodes[i].id),
            'value':1,
            'link_type': nodes[i].link_type
          });
        }
      }
    }
  }
}

function ajax_poll(poll_time){
  setTimeout(function() {
    $.getJSON(ajax_url, function(json) {
      //update d3 data element
      $("#d3_data").attr("data-d3_data", JSON.stringify(json));

      //update stack
      $("#stack_box").html(json.environment.info_box);
      set_in_progress(json.environment, json.nodes);
      needs_update = false;

      //Check Remove nodes
      remove_nodes(nodes, json.nodes);

      //Check for updates and new nodes
      json.nodes.forEach(function(d){
        current_node = findNode(d.id);
        //Check if node already exists
        if (current_node) {
          //Node already exists, just update it
          current_node.status = d.status;

          //Status has changed, image should be updated
          if (current_node.image !== d.image){
            current_node.image = d.image;
            var this_image = d3.select("#image_"+current_node.id);
            this_image
              .transition()
              .attr("x", function(d) { return d.image_x + 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x - 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x + 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x - 5; })
              .duration(100)
              .transition()
              .attr("xlink:href", d.image)
              .transition()
              .attr("x", function(d) { return d.image_x; })
              .duration(100)
              .ease("bounce");
          }

          //Status has changed, update info_box
          current_node.info_box = d.info_box;

        } else {
          addNode(d);
          build_links();
        }
      });

      //if any updates needed, do update now
      if (needs_update === true){
        update();
      }
    });
    //if no nodes still in progress, slow AJAX polling
    if (in_progress === false) { poll_time = 30000; }
    else { poll_time = 3000; }
    ajax_poll(poll_time);
  }, poll_time);
}

function update_node_name(id, name) {
  node = findNode(id);
  node.name = name;
}

function update_topo(json){
    set_in_progress(json.environment, json.nodes);
    needs_update = false;

    //Check Remove nodes
    // remove_nodes(nodes, json.nodes);
    remove_nodes(nodes, {});

    //Check for updates and new nodes

    var nID=[];
    $("#thumbnail circle").each(function(i,e){
      $(this).css("fill","black");
      var id=$(this).attr("id");
      nID.push(id);
    });

    json.nodes.forEach(function(d){
      if(nID.toString().indexOf(d.id)>-1){
        $("#thumbnail circle").each(function(i,e){
          if($(this).attr("id")==d.id){
            $(this).css("fill","red");
          }
        });
      }

      current_node = findNode(d.id);
      //Check if node already exists
      if (current_node) {
        //Node already exists, just update it
        current_node.status = d.status;
        // var need_rebuild_link=false;
        // if(current_node.required_by.length !== d.required_by.length){
        //   need_rebuild_link=true;
        // }
        // else{
        //   var not_in=true;
        //   for(var i=0;i<d.required_by.length;i++){
        //     for(var j=0;j<current_node.required_by.length;j++){
        //       if(d.required_by[i]===current_node.required_by[j]){
        //         not_in=false;
        //       }
        //     }
        //   }
        //   if(not_in){need_rebuild_link=true;}
        // }
        // if(need_rebuild_link){
        //   console.log('redraw node: '+d.id);
        //   remove_links(d.id);
        //   current_node.required_by=d.required_by;
        //   for(var j=0;j<current_node.required_by.length;j++){console.log(d.id+' new quired_by '+current_node.required_by[j])}
        //   build_link(current_node);
        // }

        //Status has changed, image should be updated
        if (current_node.image !== d.image){
          current_node.image = d.image;
          var this_image = d3.select("#image_"+current_node.id);
          this_image
            .transition()
            .attr("x", function(d) { return d.image_x + 5; })
            .duration(100)
            .transition()
            .attr("x", function(d) { return d.image_x - 5; })
            .duration(100)
            .transition()
            .attr("x", function(d) { return d.image_x + 5; })
            .duration(100)
            .transition()
            .attr("x", function(d) { return d.image_x - 5; })
            .duration(100)
            .transition()
            .attr("xlink:href", d.image)
            .transition()
            .attr("x", function(d) { return d.image_x; })
            .duration(100)
            .ease("bounce");
        }

        //Status has changed, update info_box
        current_node.info_box = d.info_box;

      } else {
        addNode(d);
        build_links();
      }
    });
    //if any updates needed, do update now
    if (needs_update === true){
      update();
    }
    if($("input[name=clone][type=submit]").length){$("g.node").click($node_click);}
}

function redraw_topo(ajax_url){
  $.getJSON(ajax_url, function(json) {
    //update d3 data element
    $("#d3_data").attr("data-d3_data", JSON.stringify(json));
    //update stack
    $("#stack_box").html(json.environment.info_box);
    set_in_progress(json.environment, json.nodes);
    needs_update = false;

    //Check Remove nodes
    remove_nodes(nodes, json.nodes);

    //Check for updates and new nodes

    var nID=[];
    $("#thumbnail circle").each(function(i,e){
      $(this).css("fill","black");
      var id=$(this).attr("id");
      nID.push(id);
    });

    json.nodes.forEach(function(d){
      if(nID.toString().indexOf(d.id)>-1){
        $("#thumbnail circle").each(function(i,e){
          if($(this).attr("id")==d.id){
            $(this).css("fill","red");
          }
        });
      }

      current_node = findNode(d.id);
      //Check if node already exists
      if (current_node) {
        //Node already exists, just update it
        current_node.status = d.status;

        //Status has changed, image should be updated
        if (current_node.image !== d.image){
          current_node.image = d.image;
          var this_image = d3.select("#image_"+current_node.id);
          this_image
            .transition()
            .attr("x", function(d) { return d.image_x + 5; })
            .duration(100)
            .transition()
            .attr("x", function(d) { return d.image_x - 5; })
            .duration(100)
            .transition()
            .attr("x", function(d) { return d.image_x + 5; })
            .duration(100)
            .transition()
            .attr("x", function(d) { return d.image_x - 5; })
            .duration(100)
            .transition()
            .attr("xlink:href", d.image)
            .transition()
            .attr("x", function(d) { return d.image_x; })
            .duration(100)
            .ease("bounce");
        }

        //Status has changed, update info_box
        current_node.info_box = d.info_box;

      } else {
        addNode(d);
        build_links();
      }
    });
    //if any updates needed, do update now
    if (needs_update === true){
      update();
    }
    if($("input[name=clone][type=submit]").length){$("g.node").click($node_click);}
  });
}

if ($(conveyor_container).length){
  var width = $(conveyor_container).width()
  if (width === 0) { width = 700;}
  var height = 500,
    //ajax_url = 'clone/get_d3_data',
    graph = $("#d3_data").data("d3_data"),
    force = d3.layout.force()
      .nodes(graph.nodes)
      .links([])
      .gravity(0.25)
      .charge(-1200)
      .linkDistance(90)
      .size([width, height])
      .on("tick", tick),
    svg = d3.select(conveyor_container).append("svg")
      .attr("width", width)
      .attr("height", height),
    node = svg.selectAll(".node"),
    link = svg.selectAll(".link"),
    needs_update = false,
    nodes = force.nodes(),
    links = force.links();
    svg.append("svg:clipPath")
             .attr("id","clipCircle")
             .append("svg:circle")
             .attr("cursor","pointer")
              .attr("r", "38px");

  svg.append("svg:defs").selectAll("marker")
    .data(["end"])      // Different link/path types can be defined here
  .enter().append("svg:marker")    // This section adds in the arrows
    .attr("id", String)
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 25)
    .attr("refY", 0)
    .attr("fill", "#999")
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
  .append("svg:path")
    .attr("d", "M0,-3L10,0L0,3");

  build_links();
  update();

  //Load initial Stack box
  $("#stack_box").html(graph.environment.info_box);

  //On Page load, set Action In Progress
  var in_progress = false;
  set_in_progress(graph.environment, node);

  //If status is In Progress, start AJAX polling
  var poll_time = 0;
  if (in_progress === true) { poll_time = 3000; }
  else { poll_time = 30000; }
  //ajax_poll(poll_time);

  //thumbnail
  var thumbnailNodes=[];
  var thumbnailEdges=[];
  for(var i=0;i<nodes.length;i++){
    thumbnailNodes.push({
      'name': nodes[i].id
    });
  }
  for(var i=0;i<links.length;i++){
    thumbnailEdges.push({
      'source':findNodeIndex(links[i].source.id),
      'target':findNodeIndex(links[i].target.id)
    });
  }
  var width = 200;
  var height = 200;
  var svgThumbnail = d3.select("#thumbnail")
      .append("svg")
      .attr("width",width)
      .attr("height",height);
  var forceThumbnail = d3.layout.force()
      .nodes(thumbnailNodes)
      .links(thumbnailEdges)
      .size([width,height])
      .linkDistance(12)
      .charge(-180);
  forceThumbnail.start();

  //add link
  var svg_edges_thumbnail = svgThumbnail.selectAll("line")
      .data(thumbnailEdges)
      .enter()
      .append("line")
      .style("stroke","#999")
      .style("stroke-width",2);
  var color = d3.scale.category20();
  //add node
  var svg_nodes_thumbnail = svgThumbnail.selectAll("circle")
      .data(thumbnailNodes)
      .enter()
      .append("circle")
      .attr("r",4)
      .style({"fill":"black","cursor":"pointer"})
      .attr("id",function(d){
        return d.name;
      })
  .call(forceThumbnail.drag);
  forceThumbnail.on("tick", function(){
    svg_edges_thumbnail.attr("x1",function(d){ return d.source.x; })
        .attr("y1",function(d){ return d.source.y; })
        .attr("x2",function(d){ return d.target.x; })
        .attr("y2",function(d){ return d.target.y; });
    svg_nodes_thumbnail.attr("cx",function(d){ return d.x; })
        .attr("cy",function(d){ return d.y; });
  });
  $("#thumbnail circle").each(function(i,e){
    $(this).hover(function(){
      $(".thbDetail").html("name:"+$(this).attr("id"));
    },function(){
      $(".thbDetail").html("");
    });
  });
}