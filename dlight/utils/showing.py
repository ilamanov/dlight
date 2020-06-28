import os.path as osp
from random import randrange
import json
import IPython.display as ipd
import dlight


def visualize_sprites(embedding, atlas, sprite_size_in_3D=None, initial_camera_z=60.0):
    """ Plot sprites from the atlas in 3D using embedding as coordinates

    Args:
        embedding ([list of tuples (x, y, z)]): The order has to follow the order
            of sprites in atlas (left to right first, then top to bottom)
        atlas ([dict]): dict with the following items:
            {
                "path": path to PNG file of atlas. Should be relative to /usr/local/share/jupyter
                        See https://stackoverflow.com/a/49487396/13344574
                "shape": {"rows": num_rows_in_atlas, "cols": num_cols_in_atlas},
                "num_sprites": number of sprites within the atlas,
                "sprite_size": {"height": height of single sprite,
                                "width": width of single sprite}
            }
        
        sprite_size_in_3D and initial_camera_z are calibration parameters
            for better visualization.
        sprite_size_in_3D ([dict]): {"height", expected height of single sprite in 3D, 
                                     "width", expected width of single sprite in 3D}
        initial_camera_z ([float]): initial z position of camera
    """
    if sprite_size_in_3D is None:
        sprite_size_in_3D = {'height': 4.0, "width": 4.0}

    data = {
        "embedding": embedding,
        "atlas": atlas,
        "sprite_size_in_3D": sprite_size_in_3D,
        "initial_camera_z": initial_camera_z
    }

    dlight.load_js_libs()
    utils_dir = osp.dirname(osp.realpath(__file__))
    ipd.display(ipd.Javascript(filename=osp.join(utils_dir, "js", "sprite_visualizer.js")))
    ipd.display(ipd.HTML(filename=osp.join(utils_dir, "js", "sprite_visualizer.css.html")))

    container_id = "sprite-visualizer-container-" + str(randrange(1000))
    ipd.display(ipd.HTML("<div id='{}'></div> ".format(container_id)))
    ipd.display(ipd.Javascript("""
            require(['sprite_visualizer'], function(sprite_visualizer) {{
                sprite_visualizer(document.getElementById("{}"), {});
            }});
        """.format(container_id, json.dumps(data))))
