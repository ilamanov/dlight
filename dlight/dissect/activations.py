import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torchvision
import dlight.utils.image as dimage


def show_activations(inputs, activations, num_cols=16, figsize=(20, 20), clf=True):
    """ Show activations along with inputs

    Args:
        inputs ([Tensor]): expected shape [B, C, H, W]
        activations ([Tensor]): expected shape [B, C, H, W]
    """
    assert inputs.shape[0] == activations.shape[0], "batch dimension should match"
    if len(inputs.shape) != 4:
        raise NotImplementedError("Only inputs of shape [B, C, H, W] (images) are supported for now")
    if len(activations.shape) != 4:
        raise NotImplementedError("Only activations of shape [B, C, H, W] are supported for now")

    inputs = inputs.detach().cpu()
    activations = activations.detach().cpu()

    num_cols = min(num_cols, activations.shape[1])
    num_rows_per_input = -(-activations.shape[1] // num_cols) # ceiling-divide https://stackoverflow.com/a/17511341/13344574
    
    if num_rows_per_input > 1:
        inputs_padded = []
        padding = torch.zeros_like(inputs[0])
        for i in range(inputs.shape[0]):
            inputs_padded.append(inputs[i])
            for j in range(num_rows_per_input - 1):
                inputs_padded.append(padding)
        inputs_padded = torch.stack(inputs_padded, dim=0)
    else:
        inputs_padded = inputs
    inputs_grid = torchvision.utils.make_grid(inputs_padded, nrow=1)

    if (num_rows_per_input * num_cols) > activations.shape[1]:
        activations_padded = []
        padding = torch.zeros_like(activations[0, 0])
        for i in range(activations.shape[0]):
            for j in range(num_rows_per_input * num_cols):
                if j < activations.shape[1]:
                    activations_padded.append(activations[i, j])
                else:
                    activations_padded.append(padding)
        activations_padded = torch.stack(activations_padded, dim=0)
        activations_padded = activations_padded[:, None, :, :]
    else:
        activations_padded = activations.view(-1, 1, activations.shape[-2], activations.shape[-1])
    activations_grid = torchvision.utils.make_grid(activations_padded, nrow=num_cols)

    # put channels dim in the back
    inputs_grid = inputs_grid.permute(1, 2, 0)
    activations_grid = activations_grid.permute(1, 2, 0)

    if clf:
        plt.clf()
    # plt.figure(figsize=figsize, dpi=80) # https://stackoverflow.com/questions/36367986/how-to-make-inline-plots-in-jupyter-notebook-larger

    f, (a0, a1) = plt.subplots(1, 2, figsize=figsize, dpi=80, gridspec_kw={'width_ratios': [1, 8]})
    a0.imshow(dimage.normalize(inputs_grid), cmap="gray", interpolation="nearest")
    a1.imshow(dimage.normalize(activations_grid), cmap="gray", interpolation="nearest")
    f.tight_layout()
    a0.axis('off')
    a1.axis('off')


def show_inputs_with_max_activation(inputs, activations, nlargest, params,
        num_cols=16, figsize=(20, 20), clf=True):
    """ See docstring of get_maximimum_activations """
    inputs = inputs.detach().cpu()
    activations = activations.detach().cpu()

    max_inputs, max_activations = \
        zip(*get_maximimum_activations(inputs, activations, nlargest, params))
    max_inputs = torch.stack(max_inputs, dim=0)

    grid = torchvision.utils.make_grid(max_inputs, nrow=num_cols)
    dimage.show_torch(dimage.normalize(grid), figsize, clf)
    print("max activations:", max_activations)


def get_maximimum_activations(inputs, activations, nlargest, params):
    """ Get nlargest max activations along with the corresponding inputs

    Args:
        inputs ([Tensor]): expected shape [B, C, H, W]
        activations ([Tensor]): expected shape [B, C, H, W] or [B, C]
        nlargest ([int]): number of largest activations to show
        params ([dict]): depends on shape of activations.
            if [B, C, H, W]:
                {
                    "outer_idx": int,
                    "reduce_func" (optional): how to reduce the grid [H, W] of conv
                            activation, one of ("mean", "max"), default is "mean"
                }
            if [B, C]:
                {
                    "outer_idx": int
                }
    
    Returns:
        [list of tuples]: (reverse) sorted by activation. Each tuple is (input, activation)
    """
    assert inputs.shape[0] == activations.shape[0], "batch dimension should match"
    if len(inputs.shape) != 4:
        raise NotImplementedError("Only inputs of shape [B, C, H, W] (images) are supported for now")

    if len(activations.shape) == 4:
        return _get_maximimum_activations_conv(inputs, activations, nlargest, params)
    elif len(activations.shape) == 2:
        return _get_maximimum_activations_fc(inputs, activations, nlargest, params)
    else:
        raise NotImplementedError("Only activations of shape [B, C, H, W] (for conv) and [B, C] (for fc) are supported for now")

def _get_maximimum_activations_conv(inputs, activations, nlargest, params):
    if "outer_idx" not in params:
        raise ValueError("outer_idx expected for conv node")
    reduce_func = params.get("reduce_func", "mean")

    activations = activations[:, params["outer_idx"]]
    activations = activations.view(activations.shape[0], -1)
    if reduce_func == "mean":
        activations = torch.mean(activations, dim=1)
    elif reduce_func == "max":
        activations = torch.max(activations, dim=1)[0]
    activations = activations.tolist()

    inputs = list(inputs)
    return sorted(zip(inputs, activations), key=lambda x: x[1], reverse=True)[:nlargest]

def _get_maximimum_activations_fc(inputs, activations, nlargest, params):
    if "outer_idx" not in params:
        raise ValueError("outer_idx expected for fully connected node")
    activations = activations[:, params["outer_idx"]].tolist()
    inputs = list(inputs)
    return sorted(zip(inputs, activations), key=lambda x: x[1], reverse=True)[:nlargest]


def show_image_superstimuli(forward_funcs, initial_input,
        optimizer_provider=None, num_iterations=100, total_variation=True,
        num_cols=16, figsize=(20, 20), clf=True,):
    """ See docstring of get_image_superstimuli """
    superstimuli = get_image_superstimuli(forward_funcs, initial_input,
        optimizer_provider, num_iterations, total_variation)
    superstimuli = torch.cat(superstimuli, dim=0)
    
    superstimuli = superstimuli.detach().cpu()

    grid = torchvision.utils.make_grid(superstimuli, nrow=num_cols)
    dimage.show_torch(dimage.normalize(grid), figsize, clf)


def get_image_superstimuli(forward_funcs, initial_input,
        optimizer_provider=None, num_iterations=100, total_variation=True):
    """ Get superstimulus for each forward_func.
        The term "superstimuli" was borrowed from
        https://distill.pub/2020/circuits/curve-detectors/#feature-visualization

    Args:
        forward_funcs ([func or list of such func]): a function that takes an input (future superstimuli)
                                                     and returns a scalar to maximize
        initial_input ([Tensor]): this will be used as the starting point for the superstimuli.
            Only inputs of type "image" are supported in this function. Must have the shape ([1, C, H, W]).
            Tensors of this shape should be consumable by forward_funcs.
            Usually initial_input is a randomly initialized Tensor which is sampled from the
            same distribution as the training input to the model.
            See Colab notebook (https://colab.research.google.com/drive/1GqynTl2NhVPMUk3LCOQ91yXGsLf1UmJj?usp=sharing)
            for example usage.

    Returns:
        [list of Tensors]: The superstimulus for each provided forward_func
    """
    assert len(initial_input.shape) == 4 and initial_input.shape[0] == 1, \
        "an image input of shape [1, C, H, W] is expected"

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    if optimizer_provider is None:
        optimizer_provider = lambda input_to_optimize: torch.optim.Adam([input_to_optimize], lr=0.1, weight_decay=1e-6)

    if not isinstance(forward_funcs, list):
        forward_funcs = [forward_funcs]

    optimized_inputs = []
    for forward_func in forward_funcs:
        initial_input_copy = initial_input.clone()
        input_to_optimize = torch.autograd.Variable(initial_input_copy, requires_grad=True)
        optimizer = optimizer_provider(input_to_optimize)
            
        for _ in range(num_iterations):
            optimizer.zero_grad()
            scalar_to_maximize = forward_func(input_to_optimize)

            loss = -scalar_to_maximize
            if total_variation:
                # for smoother superstimuli
                regularizer_coefficient = 0.0005
                loss += regularizer_coefficient * dimage.total_variation_loss(input_to_optimize[0].to(device))
            # Backward
            loss.backward()
            # Update image
            optimizer.step()

        optimized_inputs.append(input_to_optimize)
    
    return optimized_inputs
