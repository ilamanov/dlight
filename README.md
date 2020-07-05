# dlight
Tools for dissection/visualization of ConvNets.

This is the code accompanying the article titled "Explainable MNIST classification: dissection of a ConvNet" which can be found at (TODO add link).

See this [Colab notebook](https://colab.research.google.com/drive/1GqynTl2NhVPMUk3LCOQ91yXGsLf1UmJj?usp=sharing) for example usage of the code.

The code has only been tested in a Colab environment, it might not work in Jupyter notebooks or in a terminal.

## Terminology used in the code.

Meaning of "outer" and "inner" channels (or indices) of convolutions - See the arguments of [torch.nn.Conv2d](https://pytorch.org/docs/master/generated/torch.nn.Conv2d.html#torch.nn.Conv2d).
