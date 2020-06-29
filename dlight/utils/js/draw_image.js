// Use jupyter notebook --NotebookApp.iopub_data_rate_limit=10000000

// Uncomment for debugging
// require.undef("draw_image");

define("draw_image", ["d3"], function (d3) {
  return (container, data) => {
    /** data should contain the following:
     * {
     *   image_height: output image height
     *   image_width: output image width
     *   callback_name: the name of the callback to call.
     *                  the callback should have been registered with
     *                  google.colab.output.
     *                  See JS to PY communication: https://colab.research.google.com/notebooks/snippets/advanced_outputs.ipynb#scrollTo=Ytn7tY-C9U0T
     * }
     */

    const { image_height, image_width, callback_name } = data;

    const draw_color = "#fff";
    const erase_color = "#000";
    var stroke_color = draw_color;

    const erase_button_inactive_color = "#b8b7b4"; // grey
    const erase_button_active_color = "#0b8e23"; // green

    container = d3.select(container);
    const body = container.append("div");
    const footer = container.append("div").classed("draw-image-footer", true);

    var svg = body
      .append("div")
      .append("svg")
      .attr("version", "1.1")
      .attr("baseProfile", "full")
      .attr("xmlns", "http://www.w3.org/2000/svg")
      .attr("width", image_width)
      .attr("height", image_height);
    // .style("border", "1px solid grey");

    // background rect
    svg
      .append("rect")
      .attr("fill", "#000")
      .attr("width", "100%")
      .attr("height", "100%");

    // Used to extract image_array from svg
    var canvas;

    const svg_line = d3.line().curve(d3.curveBasis);
    const svg_transition = d3.transition().duration(500).ease(d3.easeLinear);
    const svg_paths_stack = new Array();

    const img_change_timeout_duration = 2000; // 2 sec
    var img_change_timeout = null;

    footer
      .append("div")
      .text("Undo")
      .classed("draw-image-undo-button", true)
      .on("click", function () {
        if (svg_paths_stack.length == 0) return;

        svg_paths_stack[svg_paths_stack.length - 1].remove();
        svg_paths_stack.splice(-1, 1);

        if (img_change_timeout !== null) {
          clearTimeout(img_change_timeout);
        }
        img_change_timeout = setTimeout(
          img_change_callback,
          img_change_timeout_duration
        );
      });

    footer
      .append("div")
      .text("Erase")
      .classed("draw-image-erase-button", true)
      .style("background-color", erase_button_inactive_color)
      .style("border", "1px solid grey")
      .style("width", "5%")
      .on("click", function () {
        const thisButton = d3.select(this);
        var isActive = !thisButton.classed("active");
        thisButton.classed("active", isActive);
        thisButton.style(
          "background-color",
          isActive ? erase_button_active_color : erase_button_inactive_color
        );
        thisButton.style(
          "border",
          isActive ? "1px solid black" : "1px solid grey"
        );
        thisButton.style("width", isActive ? "7%" : "5%");
        stroke_color = isActive ? erase_color : draw_color;
      });

    svg = svg.call(
      d3
        .drag()
        .container(function () {
          return this;
        })
        .subject(function () {
          var p = [d3.event.x, d3.event.y];
          return [p, p];
        })
        .on("start", dragstarted)
    );

    function dragstarted() {
      var d = d3.event.subject,
        active = svg
          .append("path")
          // all styles have to be inline in order to extract image array from SVG, can't store these styles in a separate file
          .attr("stroke", stroke_color)
          .attr("fill", "none")
          .attr("stroke-width", "20px")
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round")
          .datum(d),
        x0 = d3.event.x,
        y0 = d3.event.y;
      svg_paths_stack.push(active);

      d3.event.on("drag", function () {
        var x1 = d3.event.x,
          y1 = d3.event.y,
          dx = x1 - x0,
          dy = y1 - y0;

        if (dx * dx + dy * dy > 100) d.push([(x0 = x1), (y0 = y1)]);
        else d[d.length - 1] = [x1, y1];
        active.attr("d", svg_line);

        if (img_change_timeout !== null) {
          clearTimeout(img_change_timeout);
        }
        img_change_timeout = setTimeout(
          img_change_callback,
          img_change_timeout_duration
        );
      });
    }

    function img_change_callback() {
      img_change_timeout = null;

      get_image_array(async function (image_array) {
        // TODO describe how to make everything work in Jupyter on github (sync to a previous commit)

        // JS to PY communication.
        // See https://colab.research.google.com/notebooks/snippets/advanced_outputs.ipynb#scrollTo=Ytn7tY-C9U0T
        const result = await google.colab.kernel.invokeFunction(
          "notebook." + callback_name, // The callback name.
          [JSON.stringify(image_array)], // The arguments.
          {}
        ); // kwargs

        const output = result.data["application/json"];
        console.log("callback in draw_image successful. ", output);

        d3.select(canvas).remove();
      });
    }

    function get_image_array(image_array_callback) {
      const svgString = new XMLSerializer().serializeToString(svg.node());
      const svg_blob = new Blob([svgString], {
        type: "image/svg+xml;charset=utf-8",
      });

      const DOMURL = self.URL || self.webkitURL || self;
      const url = DOMURL.createObjectURL(svg_blob);

      canvas = body
        .append("canvas")
        .attr("height", image_height)
        .attr("width", image_width)
        // make it invisible
        .style("opacity", 0.0)
        .style("position", "absolute")
        .node();

      var ctx = canvas.getContext("2d");
      var img = new Image();

      img.onload = function () {
        ctx.drawImage(img, 0, 0);

        const image_data = ctx.getImageData(0, 0, image_width, image_height);
        const image_array = new Array();
        for (let y = 0; y < image_height; y++) {
          image_array.push(new Array());
          for (let x = 0; x < image_width; x++) {
            // if (y === 0 || y === (image_height - 1) ||
            //     x === 0 || x === (image_width - 1)) {
            //       image_array[y].push(255); // skip borders
            //       continue;
            //     }
            let pos = y * image_width + x;
            image_array[y].push(image_data.data[pos * 4]);
          }
        }

        image_array_callback(image_array);
      };

      img.src = url;
    }
  };
});
