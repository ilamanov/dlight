import matplotlib.pyplot as plt
import torch


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