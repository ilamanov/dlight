import dlight.dissect
import dlight.utils

import IPython.display as ipd
import dlight.utils.css_style
import os.path as osp

# to inspect require config: require.s.contexts._.config

# ipd.display(ipd.Javascript("""
#   require.config({
#     paths: {
#       d3: 'https://d3js.org/d3.v5.min'
#       }
#   });
#   """))

# The root folder (where jupyter was launched) is represented as /notebooks in jupyter notebook. That's why baseUrl is /notebooks/
ipd.display(ipd.Javascript("""
  require.config({
    baseUrl: "/notebooks/dlight/lib",
    paths: {
      d3: 'd3.v5.7.min',
      THREE: 'three.min',
      }
  });
  """))

dlight_dir = osp.dirname(osp.realpath(__file__))
ipd.display(ipd.Javascript(filename=osp.join(dlight_dir, "lib", "three_trackball_controls.js")))

ipd.display(ipd.Javascript("""
    require(['THREE', 'trackballLoader'], function(THREE, trackballLoader) {
        if (!THREE.hasOwnProperty("TrackballControls")) {
            console.log("Loading trackball controls for THREE");
            trackballLoader(THREE);
        }
    });
"""))

ipd.display(ipd.HTML(dlight.utils.css_style.global_style))