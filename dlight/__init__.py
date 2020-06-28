import dlight.dissect
import dlight.utils

import IPython.display as ipd
import dlight.utils.css_style
import os.path as osp


def load_js_libs():
  # to inspect require config: require.s.contexts._.config

  # ipd.display(ipd.Javascript("""
  #   require.config({
  #     baseUrl: "/nbextensions/dlight/lib", // see https://stackoverflow.com/a/49487396/13344574
  #     paths: {
  #       d3: 'd3.v5.7.min',
  #       THREE: 'three.min',
  #       }
  #   });
  #   """))

  ipd.display(ipd.Javascript("""
    require.config({
      paths: {
        d3: 'https://d3js.org/d3.v5.min',
        THREE: 'https://cdnjs.cloudflare.com/ajax/libs/three.js/88/three.min',
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
  