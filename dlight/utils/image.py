import os.path as osp
from random import randrange
import json
import matplotlib.pyplot as plt
import torch
import IPython.display as ipd
from google.colab import output
import dlight


def normalize(x):
    mx = torch.max(x)
    mn = torch.min(x)
    return (x - mn) / (mx - mn)
    

def show_torch(tensor, figsize=(22, 22), clf=True):
    """ Show tensor using matplotlib

    Args:
        tensor ([Tensor]): expected shape: [C, H, W]
    """
    channels = tensor.shape[0]
    if channels == 3:
        # RGB
        tensor = tensor.permute(1, 2, 0)
    elif channels == 1:
        # B&W
        tensor = tensor[0]
    else:
        raise ValueError("unsupported number of channels " + str(channels))
    if clf:
        plt.clf()
    plt.figure(figsize=figsize, dpi=80) # https://stackoverflow.com/questions/36367986/how-to-make-inline-plots-in-jupyter-notebook-larger
    plt.axis('off')
    plt.imshow(tensor, cmap="gray", interpolation="nearest")
    plt.show()


def total_variation_loss(img):
    """ 
    Args:
        img ([Tensor]): shape should be [C, H, W]
    """
    # https://towardsdatascience.com/pytorch-implementation-of-perceptual-losses-for-real-time-style-transfer-8d608e2e9902
    # https://discuss.pytorch.org/t/yet-another-post-on-custom-loss-functions/14552
    # The total variation norm formula for 2D signal images: https://www.wikiwand.com/en/Total_variation_denoising
    return torch.sum(torch.abs(img[:, :, :-1] - img[:, :, 1:])) + \
            torch.sum(torch.abs(img[:, :-1, :] - img[:, 1:, :]))


def draw_synthetic_input(input_height, input_width, callback):
    """ Draw synthetic input and call the provided callback
        with the image array when image is changed.

    Args:
        input_height ([int]): height of the input image
        input_width ([int]): width of the input image
        callback ([func]): callback to call when drawn image is changed.
            The only argument to the callback will be a 2D image_array
            with grayscale values of type int within [0, 255]
    """
    def draw_synthetic_input_callback(x):
        x = json.loads(x) # parse json from string
        callback(x)
        return ipd.JSON({'result': "parsed synthetic input"})

    # JS to PY communication.
    # See https://colab.research.google.com/notebooks/snippets/advanced_outputs.ipynb#scrollTo=Ytn7tY-C9U0T
    output_callback_name = "draw_synthetic_input_callback_" + str(randrange(1000))
    output.register_callback(
        'notebook.' + output_callback_name, draw_synthetic_input_callback)

    dlight.load_js_libs()
    utils_dir = osp.dirname(osp.realpath(__file__))
    ipd.display(ipd.Javascript(filename=osp.join(utils_dir, "js", "draw_image.js")))
    ipd.display(ipd.HTML(filename=osp.join(utils_dir, "js", "draw_image.css.html")))
    
    data = {
        "image_height": input_height,
        "image_width": input_width,
        "callback_name": output_callback_name
    }
    
    container_id = "draw-image-container-" + str(randrange(1000))
    ipd.display(ipd.HTML("<div id='{}'></div> ".format(container_id)))
    ipd.display(ipd.Javascript("""
            require(['draw_image'], function(draw_image) {{
                draw_image(document.getElementById("{}"), {});
            }});
        """.format(container_id, json.dumps(data))))
        