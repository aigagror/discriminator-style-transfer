import torch
from torch import nn
from torch.nn.utils.spectral_norm import SpectralNorm

import utils


class StyleLayerKernel(nn.Module):
    def __init__(self, cnn_chunk, style_feats, kernel, k):
        """
        Initialize kernel.

        Args:
            self: (todo): write your description
            cnn_chunk: (todo): write your description
            style_feats: (todo): write your description
            kernel: (todo): write your description
            k: (int): write your description
        """
        super().__init__()

        self.conv = cnn_chunk
        batch_size, channels, height, width = style_feats.shape
        assert batch_size == 1

        style_feats = style_feats.view(channels, height * width).t()
        self.style_feats = torch.tanh(style_feats)
        assert style_feats.requires_grad == False

        self.kernel = kernel
        self.k = k

    def forward(self, inp):
        """
        Forward function.

        Args:
            self: (todo): write your description
            inp: (todo): write your description
        """
        x, kernel_outs = inp
        feat_maps = self.conv(x)
        batch_size, channels, height, width = feat_maps.shape
        assert batch_size == 1

        cnn_feats = feat_maps.view(channels, height * width).t()
        cnn_feats = torch.tanh(cnn_feats)

        gen_sample, style_sample = utils.sample_k(cnn_feats, self.style_feats, k=self.k)
        kernel_out = self.kernel(gen_sample, style_sample)
        kernel_outs.append(kernel_out)
        return (feat_maps, kernel_outs)


class StyleLayerDisc(nn.Module):
    def __init__(self, mode, cnn_chunk, out_c, k, h_dim=256):
        """
        Initialize a chunk.

        Args:
            self: (todo): write your description
            mode: (todo): write your description
            cnn_chunk: (todo): write your description
            out_c: (str): write your description
            k: (int): write your description
            h_dim: (int): write your description
        """
        super().__init__()

        self.conv = cnn_chunk
        self.k = k
        self.mode = mode

        # Discriminator
        self.disc = nn.Sequential(
            nn.Linear(out_c, h_dim),
            nn.ReLU(),
            nn.Linear(h_dim, h_dim),
            nn.ReLU(),
            nn.Linear(h_dim, 1),
        )
        if mode == 'sn':
            for module in self.disc.modules():
                if isinstance(module, nn.Linear):
                    SpectralNorm.apply(module, 'weight', n_power_iterations=1, eps=1e-12, dim=0)
        else:
            assert mode == 'wass'

    def forward(self, inp):
        """
        Forward computation.

        Args:
            self: (todo): write your description
            inp: (todo): write your description
        """
        x, disc_outs = inp
        # Spatial features
        cnn_feats = self.conv(x)
        bsz, c, h, w = cnn_feats.size()

        # Discriminator
        disc_inp = torch.tanh(cnn_feats.view(c, -1).t())
        disc_inp = utils.sample_k(disc_inp, k=self.k)
        d = self.disc(disc_inp)
        disc_outs.append(torch.mean(d))

        return (cnn_feats, disc_outs)

    def disc_gp(self, x):
        """
        Discretize the gradient of x.

        Args:
            self: (todo): write your description
            x: (array): write your description
        """
        with torch.no_grad():
            # Spatial features
            cnn_feats = self.conv(x)
            bsz, c, h, w = cnn_feats.size()

            # Discriminator
            disc_inp = torch.tanh(cnn_feats.view(c, -1).t())

        # Gradient Penalty
        gp = utils.calc_gradient_penalty(self.disc, disc_inp)

        return cnn_feats, gp

