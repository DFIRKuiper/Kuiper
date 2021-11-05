
function graph(selector , _options){
    var container_name, width, height, radius, Nodes, Links, container, svg, force
    var func = {
      createNode: createNode,
      createLink: createLink,
      drawNode: drawNode,
      drawLink: drawLink
    }
    options = {
      width: 100,
      height:100,
      radius: 10,
      on_node_click: undefined,
      on_node_start_drag: undefined,
      on_node_drag: undefined,
      on_node_end_drag: undefined,
      on_node_mouseover: undefined,
      on_node_mouseout: undefined,
      tick: undefined,
      on_container_click: undefined
    }

    merge_obj(options , _options)

    function init(c){
        container_name = c;
        width = options.width;
        height = options.height;
        radius = options.radius;


        Nodes = []
        Links = []
        
        container = d3.select(container_name).append("svg")
            .attr("width","100%")
            .attr("height","100%")
            .attr('viewBox' , [-width/2 , -height/2 , width , height])
        
        svg = container.append("g")
            .attr("class", "everything")


        // on click any place on the container
        container.on('click' , function(){

          if (typeof options.on_container_click === 'function') options.on_container_click(this);
        })

        force = d3.forceSimulation()
            .velocityDecay(0.7)
            .force("links",d3.forceLink().id(function(d){return d.id}))
            .force("charge",d3.forceManyBody().strength(-150 * radius))


        // add zoom capabilities 
        var zoom_handler = d3.zoom().on("zoom", function(){
                svg.attr("transform", d3.event.transform)
        });
        zoom_handler(container);     


        force.nodes(Nodes).on("tick", ticked);


    }

    // call init function
    init(selector , options.width, options.height)

    // copy all object properties from source to target
    function merge_obj(target, source) {
        Object.keys(source).forEach(function(property) {
            target[property] = source[property];
        });
    }

    // tick function
    function ticked(){
        // circle node
        svg.selectAll("circle.node")
            .attr("cx", d=> d.x)
            .attr("cy", d=> d.y);

        // circle text
        svg.selectAll("g.group_node text.label")
            .attr("x", d=> d.x)
            .attr("y", d=> d.y+2);


        // line
        svg.selectAll("line")
            .attr("x1", d=> d.source.x)
            .attr("y1", d=> d.source.y)
            .attr("x2", d=> d.target.x)
            .attr("y2", d=> d.target.y)


        // line label
        svg.selectAll("g.group_link text.label")
          .attr("x", d=> (d.target.x + d.source.x)/2 )
          .attr("y", d=> (d.target.y + d.source.y)/2 )


            

        // apply function tick by user
        if (typeof options.tick === 'function') options.tick(this);
    }


    function get_node_if_exists(id){
      for(var i = 0 ; i < Nodes.length ; i++){
        if (Nodes[i]['id'] == id) return Nodes[i];
      }
      return false;
    }

    function get_link_if_exists(id){
      for(var i = 0 ; i < Links.length ; i++){
        if (Links[i]['id'] == id) return Links[i];
      }
      return false;
    }

    // add node to the list of nodes, but it will not draw it
    function createNode(id , type , properities){
        if (get_node_if_exists(id)){
          console.log('[-] Nodes ['+id+'] exists')
          return;
        }

        var n = {
          id: id,
          type: type,
          properities: properities,
          radius: 15,
          visible: false
        }
        Nodes.push(n)

    }

    // add a link to the list of links
    function createLink( id, src, dst , label){
      // node cannot be linked to itself
      if(src == dst){
        console.log("[-] Error: source and target nodes cannot be same")
        return;
      }
      // get the source and target nodes
      var src = get_node_if_exists(src)
      var dst = get_node_if_exists(dst)
      if(src == false || dst == false){
        console.log("[-] Error: source node or target node not exists")
        return;
      }

        var l = {
          id: id,
          source: src,
          target: dst,
          label: label,
          distance: 50
        }
        Links.push(l)

    }

    // add a node to the svg
    function drawNode(Nodes_indx){
        var n = get_node_if_exists(Nodes_indx)
        if(n == false){
            console.log('[-] Node ['+Nodes_indx+'] not exists')
            return;
        }


        // if node already shown no need to draw it again
        if(n['visible']) return;


        // NODE
        var node = svg.append('g')
            .attr('class' , 'group_node')
                .data([ n ])
            .attr('id' , n['id'])
            // .attr("cx", function (d) {console.log(d); return d.x;})
            // .attr("cy", function (d) {return d.y;})

            .call(d3.drag() // <-D
                        .on("start", dragStarted)
                        .on("drag", dragged )
                        .on("end", dragEnded))

            // on node mouse over
            .on('mouseover', function(d , i) { 
                  var cir = d3.select(this).select('circle')
                      .transition()
                      .duration(100)
                      .attr('r', d.radius * 1.4)
                      .style('stroke' , '#999')
                      .style('cursor' , 'grabbing')

                  if (typeof options.on_node_mouseover === 'function') options.on_node_mouseover(this);

                } )
            // on node mouse out
            .on('mouseout',  function(d , i) { 
                  var cir = d3.select(this).select('circle')
                      .transition()
                      .duration(100)
                      .attr('r', d.radius ) 
                      .style('stroke' , 'none')

                  if (typeof options.on_node_mouseout === 'function') options.on_node_mouseout(this);
                } )

            // on node clicked
            .on('click' , function(d){


                if (typeof options.on_node_click === 'function') options.on_node_click(this);
            })


        // CIRCLE
        node.append("circle")
            .attr("class", d => "node " + getNodeClass(d.type))
                .transition()
            .attr("r", d => d.radius)
                .transition()


        //TEXT
        node.append("text")
              .text(function(d, i) { return d.type; })
              .attr("class", "label")

        // assign the node as visible in svg
        n['visible'] = true;
        //this.force.restart()
        force.nodes(Nodes).on("tick", ticked);
    }



    // add a link to the svg
    function drawLink(Link_indx){

        var l = get_link_if_exists(Link_indx)
        if(l == false){
            console.log('[-] Link ['+Link_indx+'] not exists')
            return;
        }
        console.log(l)
        // GROUP
        var group = svg.append("g")
              .attr("class" , "group_link")
                  .data([ l ])


        // LINK
        group.append("line") // <-B
              .data([ l ])
            .attr("class", "line")
            .attr("x1", function (d) { console.log(d); return d.source.x;})
            .attr("y1", function (d) {return d.source.y;})
            .attr("x2", function (d) {return d.target.x;})
            .attr("y2", function (d) {return d.target.y;})

              .transition()
              .delay(100)

        // LABEL
        group.append("text")
              .text(function(d, i) { return d.label; })
              .attr("class", "label")


        force.force("links").links( Links )
    }



    // on node start dragged
    function dragStarted(d) {
        if (!d3.event.active) {
            force.alphaTarget(0.9).restart();
        }
        d.fx = d.x; // <-E
        d.fy = d.y;

        if (typeof options.on_node_start_drag === 'function') options.on_node_start_drag(d);
    }

    // on node drag
    function dragged(d) {
        // if (!d3.event.active)
        //     force.alphaTarget(0.3).restart();

        d.fx = d3.event.x; // <-F
        d.fy = d3.event.y;
        //this.force.on("tick", function(){console.log('ticked')});
        //console.log( this )
        if (typeof options.on_node_drag === 'function') options.on_node_drag(d);
    }

    // on node end drag 
    function dragEnded(d) {
        if (!d3.event.active)
            force.alphaTarget(0);

        if (typeof options.on_node_end_drag === 'function') options.on_node_end_drag(d);
        // d.fx = null;
        // d.fy = null;
        
    }



    // get the node class based on its type
    function getNodeClass(type){
        type = type.toLowerCase() 
        switch (type){
          case "mft"              : return "node_class_lightblue";
          case "usnjrl"           : return "node_class_green";
          case "windows_events"   : return "node_class_lightpink";
          case "userassist"       : return "node_class_purple";
          case "shimcache"        : return "node_class_lightred";
          case "WordWheelQuery"   : return "node_class_lightyellow";
          case "BAM"              : return "node_class_lightorange";
          case "shellbags"        : return "node_class_navyblue";
          case "TypedPaths"       : return "node_class_darkgray";
          case "runmru"           : return "node_class_green2";
          case "amcache"          : return "node_class_darkpurple";
          case "appcompatflags"   : return "node_class_lightgray";
          case "ComputerName"     : return "node_class_darkred";
          case "Launching_tracing": return "node_class_darkpink";
          case "TimeZone"         : return "node_class_darkorange";

          
          default: return "";
        }
    }
    // return list of functions
    return func 
}