import os.path as osp
from random import randrange
import json
import IPython.display as ipd
import dlight


def draw_synthetic_input(input_height, input_width, callback_name):
    """ Draw synthetic input and call the provided callback
       with the image array.

    Args:
        input_height ([int]): height of the input image
        input_width ([int]): width of the input image
        callback_name ([str]): the name of the function to call
        with the image array. Function must be defined in the notebook.
    """

    data = {
        "image_height": input_height,
        "image_width": input_width,
        "callback_name": callback_name
    }

    dlight.load_js_libs()
    dissect_dir = osp.dirname(osp.realpath(__file__))
    ipd.display(ipd.Javascript(filename=osp.join(dissect_dir, "js", "draw_image.js")))
    ipd.display(ipd.HTML(filename=osp.join(dissect_dir, "js", "draw_image.css.html")))

    container_id = "draw-image-container-" + str(randrange(1000))
    ipd.display(ipd.HTML("<div id='{}'></div> ".format(container_id)))
    ipd.display(ipd.Javascript("""
            require(['draw_image'], function(draw_image) {{
                draw_image(document.getElementById("{}"), {});
            }});
        """.format(container_id, json.dumps(data))))