import torch.nn as nn
import torchvision
import dlight.utils.image as dimage

# TODO describe in Terminology page on github what is outer and inner idx

def show_weights(node, params, num_cols=16, figsize=(20, 20), clf=True):
    """ Show weights of the node.

    Args:
        node ([subclass of nn.Module]): For example, nn.Conv2d, nn.Linear
        params ([dict]): content of the dict depends on the type of node.
            See below for supported types.
        if nn.Conv2d:
            {
                outer_idx (optional): ([int])
            }
    """
    node = node.cpu()
    if isinstance(node, nn.Conv2d):
        _show_conv2d_weights(node, params, num_cols, figsize, clf)
    else:
        raise NotImplementedError("Type " + node.__class__.__name__ + " is not supported yet")


def _show_conv2d_weights(node, params, num_cols, figsize, clf):
    outer_idx = params.get("outer_idx", None)

    w = node.weight.data
    if outer_idx is not None:
        w = w[outer_idx:outer_idx + 1]
    w = w.view(-1, 1, w.shape[-2], w.shape[-1])
    
    grid = torchvision.utils.make_grid(w, nrow=num_cols)
    dimage.show_torch(dimage.normalize(grid), figsize, clf)

    if node.bias is not None:
        b = node.bias.data
        if outer_idx is not None:
            b = b[outer_idx]
        print("bias:", b)