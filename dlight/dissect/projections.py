import os
import os.path as osp
from random import randrange
import uuid
import imageio
import math
import torch
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
# from umap import UMAP
import dlight.utils.showing as showing


# (From sklearn.manifold.TSNE documentation):
# It is highly recommended to use another dimensionality reduction method 
# (e.g. PCA for dense data or TruncatedSVD for sparse data) to reduce the 
# number of dimensions to a reasonable amount (e.g. 50) if the number of 
# features is very high. This will suppress some noise and speed up the 
# computation of pairwise distances between samples. For more tips see Laurens van der Maaten’s FAQ [2].
# https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
# https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html
# https://github.com/YaleDHLab/pix-plot/blob/master/utils/process_images.py
# https://umap-learn.readthedocs.io/en/latest/parameters.html
# https://towardsdatascience.com/a-one-stop-shop-for-principal-component-analysis-5582fb7e0a9c
# https://arxiv.org/pdf/1802.03426.pdf
def project_fc_activations(inputs, activations, projections_pipe):
    """ Visualize the embedding of the inputs.
        Activations are treated as embeddings.

    Args:
        inputs ([Tensor]): RGBA images. Expected shape [B, 4, H, W]
        activations ([Tensor]): Embdeding to use for visualization. Expected shape [B, C]
        projections_pipe ([list of dicts]): Pipe of projections: output of one projection
            will be the input to the following projection.
            Each dict should contain the following:
            {
                "type" (str): type of projection (one of [t-sne, pca, umap]),
                "n_components" (int): dimensionality of the projection
            }
    """
    assert len(inputs.shape) == 4 and inputs.shape[1] == 4, \
        "inputs must be RGBA -> shape= [B, 4, H, W]. Instead got: " + str(inputs.shape)
    assert len(activations.shape) == 2, \
        "Only outputs of fully connected nodes (of shape [B, C]) are supported in this function"
    assert inputs.shape[0] == activations.shape[0]

    inputs = inputs.detach().cpu()
    activations = activations.detach().cpu()

    num_images = inputs.shape[0]
    image_height = inputs.shape[2]
    image_width = inputs.shape[3]  
    
    # Build the atlas grid
    atlas_number_of_cols = int(math.ceil(math.sqrt(num_images)))
    atlas_number_of_rows = atlas_number_of_cols

    atlas = torch.zeros((4, image_height * atlas_number_of_rows, image_width * atlas_number_of_cols))
    for y in range(atlas_number_of_rows):
        for x in range(atlas_number_of_cols):
            img_idx = y * atlas_number_of_cols + x
            if img_idx < num_images:
                img_RGBA = inputs[img_idx]
                y_offset = y * image_height
                x_offset = x * image_width
                atlas[:, y_offset : y_offset + image_height, x_offset : x_offset + image_width] = img_RGBA

    # We need to put the image in jupyter dir to access it from Javascript.
    # See https://stackoverflow.com/a/49487396/13344574
    jupyter_dir = osp.abspath("/usr/local/share/jupyter")
    atlas_path = osp.join(
        "nbextensions", "tmp", "atlas_" + str(uuid.uuid4()) + ".png")

    atlas_dir = osp.dirname(osp.join(jupyter_dir, atlas_path))
    if not osp.exists(atlas_dir):
        os.makedirs(atlas_dir)
    
    atlas = (atlas * 255.0).byte() # convert to uint8
    imageio.imwrite(osp.join(jupyter_dir, atlas_path), atlas.permute(1, 2, 0).numpy())
    
    embedding = activations.numpy()
    print("Shape of initial embedding = ", embedding.shape)
    for projection in projections_pipe:
        projection_type = projection["type"]
        projection_n_components = projection["n_components"]

        if projection_n_components > embedding.shape[1]:
            raise ValueError("n_components for " + projection_type + 
                " has to be <= " + embedding.shape[1] + 
                ", which is the dimensionality of the previous projection")
        if projection_type == "t-sne":
            tsne = TSNE(n_components=projection_n_components)
            embedding = tsne.fit_transform(embedding)
        elif projection_type == "pca":
            pca = PCA(n_components=projection_n_components)
            embedding = pca.fit_transform(embedding)
        # elif projection_type == "umap":
        #     umap = UMAP(n_components=projection_n_components, n_neighbors=25, min_dist=0.00001, metric='correlation')
        #     embedding = umap.fit_transform(embedding)
        else:
            raise NotImplementedError("projection type = " + projection_type + " is not supported yet")
        print("Shape after " + projection_type + " = " + str(embedding.shape))

    # if final embedding dimension is 2D, add a fake third dimension (which is 0 for all)
    # so that it's compatible with the JS visualization library
    if embedding.shape[1] == 2:
        embedding3d = torch.zeros((num_images, 3))
        embedding3d[:, :2] = embedding
        embedding = embedding3d
    
    # Some calibration. This was calibrated for MNIST.
    # Might need to be adjusted for other datasets.
    random_embedding = embedding[randrange(num_images)]
    distance_from_origin = torch.norm(torch.from_numpy(random_embedding)).item()
    sprite_size_in_3D = {'height': distance_from_origin / 5.0, "width": distance_from_origin / 5.0}
    initial_camera_z = 3.0 * distance_from_origin

    embedding = embedding.tolist()

    showing.visualize_sprites(
        embedding,
        {
            "path": atlas_path,
            "shape": {"rows": atlas_number_of_rows, "cols": atlas_number_of_cols},
            "num_sprites": num_images,
            "sprite_size": {"height": image_height, "width": image_width}
        },
        sprite_size_in_3D,
        initial_camera_z)