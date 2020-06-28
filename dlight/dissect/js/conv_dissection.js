// Use jupyter notebook --NotebookApp.iopub_data_rate_limit=10000000

// Uncomment for debugging
// require.undef("conv_dissection");

define("conv_dissection", ["d3"], function (d3) {
  return (container, data) => {
    /** data should contain the following:
     * {
     *   // below are all nested lists of floats
     *   input_to_conv: shape = (B, NUM_IN_CHANNELS, H, W),
     *   weights: shape = (1, NUM_IN_CHANNELS, H, W),
     *   intermediate_activations: shape = (B, NUM_IN_CHANNELS, H, W),
     *   cumulative_activations: shape = (B, NUM_IN_CHANNELS + 1(for bias), H, W),
     *   activation: shape = (B, 1, H, W),
     *
     *   bias: float
     *   input_description (optional): dict mapping from idx (1-based)
     *                                 of inner channels to description
     * }
     */

    // ----------------------------- Init -----------------------------
    const {
      input_to_conv,
      weights,
      bias,
      intermediate_activations,
      cumulative_activations,
      activation,
    } = data;
    const input_description = data.input_description
      ? data.input_description
      : null;

    const inner_container = d3
      .select(container)
      .append("div")
      .attr("class", "conv-dissection-inner-container");

    const num_in_channels = input_to_conv[0].length;
    const input_height = input_to_conv[0][0].length;
    const input_width = input_to_conv[0][0][0].length;
    const weight_height = weights[0][0].length;
    const weight_width = weights[0][0][0].length;
    const activation_height = activation[0][0].length;
    const activation_width = activation[0][0][0].length;

    // ----------------------------- Add empty columns -----------------------------

    function add_column(title, content_class = null) {
      const column = inner_container
        .append("div")
        .attr("class", "conv-dissection-column");
      column
        .append("div")
        .attr("class", "conv-dissection-column-title")
        .text(title);

      return column
        .append("div")
        .attr(
          "class",
          "conv-dissection-column-content" +
            (content_class ? " " + content_class : "")
        );
    }

    const input_content = add_column("Input to conv");

    var input_description_content;
    if (input_description) {
      input_description_content = add_column(
        "Input description",
        "conv-dissection-description-column-content"
      );
    }

    const indices_content = add_column(
      "idx",
      "conv-dissection-indices-column-content"
    );

    const weights_content = add_column("Weights");
    const intermediate_activations_content = add_column(
      "Intermediate activations"
    );
    const cumulative_activations_content = add_column("Cumulative activations");
    const output_content = add_column(
      "Output",
      "conv-dissection-output-column-content"
    );

    // ----------------------------- Populate columns -----------------------------

    function populate_image_column(
      content_node,
      content_data,
      canvas_class,
      canvas_size
    ) {
      const pixelated_threshold = 10;

      const verticals = content_node
        .selectAll(".column-content-verticals")
        .data(content_data)
        .enter()
        .append("div")
        .attr(
          "class",
          "column-content-verticals conv-dissection-vertical-content"
        );

      const horizontals = verticals
        .selectAll(".column-content-horizontals")
        .data((d) => d)
        .enter()
        .append("canvas")
        .attr("class", "column-content-horizontals " + canvas_class)
        .attr("height", canvas_size[0])
        .attr("width", canvas_size[1]);
      // .on("mousemove", mousemove)
      // .on("mouseout", mouseout)

      if (
        canvas_size[0] < pixelated_threshold &&
        canvas_size[1] < pixelated_threshold
      ) {
        horizontals.style("image-rendering", "pixelated");
      }

      populateCanvasNodes(
        horizontals.nodes(),
        get_column_color_scale(content_data)
      );

      return verticals;
    }

    function populate_text_column(content_node, content_data, text_class) {
      const verticals = content_node
        .selectAll(".column-content-verticals")
        .data(content_data)
        .enter()
        .append("div")
        .attr(
          "class",
          "column-content-verticals conv-dissection-vertical-content"
        );

      verticals
        .selectAll(".column-content-horizontals")
        .data((d) => d)
        .enter()
        .append("div")
        .text((d) => d)
        .attr("class", "column-content-horizontals " + text_class);
    }

    populate_image_column(input_content, input_to_conv, "input-canvas", [
      input_height,
      input_width,
    ]);

    if (input_description) {
      const input_description_array = [];
      for (let i = 0; i < num_in_channels; i++) {
        input_description_array.push(input_description[i + 1]);
      }

      populate_text_column(
        input_description_content,
        [input_description_array],
        "input-description-text"
      );
    }

    const idx_data = [];
    for (let i = 0; i < num_in_channels; i++) {
      idx_data.push(i + 1);
    }
    populate_text_column(indices_content, [idx_data], "index-text");

    const weight_verticals = populate_image_column(
      weights_content,
      weights,
      "weight-canvas",
      [weight_height, weight_width]
    );
    weight_verticals.append("div").text(`Bias = ${bias.toFixed(4)}`);

    populate_image_column(
      intermediate_activations_content,
      intermediate_activations,
      "intermediate-act-canvas",
      [activation_height, activation_width]
    );

    populate_image_column(
      cumulative_activations_content,
      cumulative_activations,
      "cumulative-act-canvas",
      [activation_height, activation_width]
    );

    populate_image_column(output_content, activation, "output-canvas", [
      activation_height,
      activation_width,
    ]);

    // ----------------------------- Helper functions -----------------------------

    function populateCanvasNodes(nodes, colorScale) {
      for (let i = 0; i < nodes.length; i++) {
        let canvas = nodes[i];
        let imageArray = d3.select(canvas).data()[0];
        if (imageArray === null) continue;

        let context = canvas.getContext("2d");

        let image = context.createImageData(
          imageArray.length,
          imageArray[0].length
        );

        populateCanvasImage(image, imageArray, colorScale);

        context.putImageData(image, 0, 0);
      }
    }

    function populateCanvasImage(canvasImage, imageArray, colorScale) {
      // expected shape of image array = [height, width]
      for (let y = 0; y < imageArray.length; y++) {
        for (let x = 0; x < imageArray[0].length; x++) {
          let pos = y * imageArray[0].length + x;
          let c = colorScale(imageArray[y][x]);
          canvasImage.data[pos * 4 + 0] = c; // R
          canvasImage.data[pos * 4 + 1] = c; // G
          canvasImage.data[pos * 4 + 2] = c; // B
          canvasImage.data[pos * 4 + 3] = 255; // A
        }
      }
    }

    function get_column_color_scale(column_data) {
      /**
       * column_data shape is (B, NUM_IN_CHANNELS, H, W)
       */
      let overallMin = Infinity;
      let overallMax = -Infinity;
      for (let img_idx = 0; img_idx < column_data.length; img_idx++) {
        for (let in_idx = 0; in_idx < column_data[0].length; in_idx++) {
          for (let y = 0; y < column_data[0][0].length; y++) {
            for (let x = 0; x < column_data[0][0][0].length; x++) {
              let weightVal = column_data[img_idx][in_idx][y][x];
              if (weightVal < overallMin) overallMin = weightVal;
              if (weightVal > overallMax) overallMax = weightVal;
            }
          }
        }
      }

      const color_scale = d3
        .scaleLinear()
        .domain([overallMin, overallMax])
        .range([0, 255]);
      return color_scale;
    }
  };
});
