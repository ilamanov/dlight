import os.path as osp
import json
import IPython.display as ipd


utils_dir = osp.dirname(osp.realpath(__file__))
ipd.display(ipd.Javascript(filename=osp.join(utils_dir, "js", "sprite_visualizer.js")))
ipd.display(ipd.HTML(filename=osp.join(utils_dir, "js", "sprite_visualizer.css.html")))


def visualize_sprites(embedding, atlas, sprite_size_in_3D=None, initial_camera_z=60.0):
    """ Plot sprites from the atlas in 3D using embedding as coordinates

    Args:
        embedding ([list of tuples (x, y, z)]): The order has to follow the order
            of sprites in atlas (left to right first, then top to bottom)
        atlas ([dict]): dict with the following items:
            {
                "path": path to PNG file of atlas. Should be relative to the root dir of the Jupyter notebook
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

    # The root folder (where jupyter was launched) is represented as /notebooks in jupyter notebook. That's why baseUrl is /notebooks/
    atlas["path"] = '/notebooks/' + atlas["path"]

    data = {
        "embedding": embedding,
        "atlas": atlas,
        "sprite_size_in_3D": sprite_size_in_3D,
        "initial_camera_z": initial_camera_z
    }

    ipd.display(ipd.Javascript("""
            (function(element){{
                require(['sprite_visualizer'], function(sprite_visualizer) {{
                    sprite_visualizer(element.get(0), {});
                }});
            }})(element);
        """.format(json.dumps(data))))
