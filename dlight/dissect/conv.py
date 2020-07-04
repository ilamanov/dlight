import os.path as osp
from random import randrange
import json
import IPython.display as ipd
import torch
import torch.nn as nn
import dlight


def show_conv_dissection(input_to_conv, node, outer_idx, input_description=None):
    """ Conv dissection consists of the following columns (TODO see medium article for definition of each column, also which section):
        - input to convolutional layer
        - (optional) description of the input
        - index of each input to convolutional layer
        - weights of each inner channel of conv_outer_idx
        - intermediate activations 
        - cumulative activations
        - output

    Args:
        input_to_conv ([Tensor]): expected shape [B, C, H, W]
        node ([nn.Conv2d]): conv node
        outer_idx ([int]): outer index of the conv node
        input_description ([dict]): mappping from (1-based) index of conv
            inner channels to the description of the corresponding input.
    """
    
    input_to_conv, weights, bias, intermediate_activations, activation = \
        get_conv_dissection(input_to_conv, node, outer_idx)

    num_images = input_to_conv.shape[0]
    num_inner_channels = input_to_conv.shape[1]
    cumulative_activations = []
    for img_idx in range(num_images):
        cumulative = [intermediate_activations[img_idx, 0]]
        for inner_idx in range(1, num_inner_channels):
            cumulative.append(cumulative[inner_idx - 1] + intermediate_activations[img_idx, inner_idx])
        cumulative.append(cumulative[num_inner_channels - 1] + bias)
        for i in range(len(cumulative)):
            cumulative[i] = cumulative[i].tolist()
        cumulative_activations.append(cumulative)

    data = {
        "input_to_conv": input_to_conv.tolist(), # shape = (B, NUM_IN_CHANNELS, H, W)
        "weights": weights.tolist(), # shape = (1, NUM_IN_CHANNELS, H, W)
        "bias": bias,
        "intermediate_activations": intermediate_activations.tolist(), # shape = (B, NUM_IN_CHANNELS, H, W)
        "cumulative_activations": cumulative_activations, # shape = (B, NUM_IN_CHANNELS + 1(for bias), H, W)
        "activation": activation.tolist() # shape = (B, 1, H, W)
    }

    if input_description is not None:
        data["input_description"] = input_description

    dlight.load_js_libs()
    dissect_dir = osp.dirname(osp.realpath(__file__))
    ipd.display(ipd.Javascript(filename=osp.join(dissect_dir, "js", "conv_dissection.js")))
    ipd.display(ipd.HTML(filename=osp.join(dissect_dir, "js", "conv_dissection.css.html")))

    container_id = "conv-dissection-container-" + str(randrange(1000))
    ipd.display(ipd.HTML("<div id='{}'></div> ".format(container_id)))
    ipd.display(ipd.Javascript("""
            require(['conv_dissection'], function(conv_dissection) {{
                conv_dissection(document.getElementById("{}"), {});
            }});
        """.format(container_id, json.dumps(data))))


def get_conv_dissection(input_to_conv, node, outer_idx):
    """ See docstring of show_conv_dissection """
    assert isinstance(node, nn.Conv2d)
    assert len(input_to_conv.shape) == 4, "input_to_conv must be of shape [B, C, H, W]"

    num_inner_channels = input_to_conv.shape[1]
    
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    input_to_conv = input_to_conv.to(device)

    weights = node.weight.data[outer_idx:outer_idx + 1]
    bias = 0.0
    if node.bias is not None:
        bias = node.bias.data[outer_idx].item()

    intermediate_activations = []
    for inner_idx in range(num_inner_channels):
        intermediate_conv = nn.Conv2d(1, 1,
                kernel_size=node.kernel_size, stride=node.stride, padding=node.padding)
        intermediate_conv.weight.data = \
            node.weight.data[outer_idx:outer_idx + 1, inner_idx:inner_idx + 1, :, :].clone()
        intermediate_conv.bias.data[0] = 0.0
        intermediate_conv = intermediate_conv.to(device)

        intermediate_activations.append(
            intermediate_conv(input_to_conv[:, inner_idx:inner_idx + 1, :, :]))

    intermediate_activations = torch.cat(intermediate_activations, dim=1) # now shape is [B, NUM_IN_CHANNELS, H, W]

    activation = node(input_to_conv)[:, outer_idx:outer_idx + 1, :, :]

    # [ torch.sum(intermediate_activations, dim=1) + bias = activation ] should hold true

    return input_to_conv, weights, bias, intermediate_activations, activation


