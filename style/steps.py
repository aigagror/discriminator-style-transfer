import utils

import torch
from torch.nn import functional as F

def disc_step(model, opt, gen_img, style_img):
    """
    Perform a single optimization step.

    Args:
        model: (todo): write your description
        opt: (todo): write your description
        gen_img: (int): write your description
        style_img: (str): write your description
    """
    model.train()
    opt.zero_grad()

    d_real, _ = model(style_img)
    d_gen, _ = model(gen_img)

    if model.disc_mode == 'wass':
        # Wasserstein Distance
        dist = d_gen - d_real

        # Gradient Penalty
        x = utils.interpolate(gen_img, style_img)
        gp = model.disc_gp(x)

        loss = dist + 10 * gp
    else:
        assert model.disc_mode == 'sn', model.disc_mode
        # Spectral norm
        real_loss = F.binary_cross_entropy_with_logits(d_real, torch.ones_like(d_real))
        gen_loss = F.binary_cross_entropy_with_logits(d_gen, torch.zeros_like(d_gen))
        loss = real_loss + gen_loss

    loss.backward()

    opt.step()
    return loss.item()


def sc_step(model, opt, gen_img, args):
    """
    Perform an optimization step.

    Args:
        model: (todo): write your description
        opt: (todo): write your description
        gen_img: (int): write your description
    """
    model.eval()
    opt.zero_grad()

    if args.distance.startswith('disc-'):
        disc_real, content_loss = model(gen_img)
        style_loss = -disc_real
    else:
        style_loss, content_loss = model(gen_img)

    loss = args.alpha * style_loss + (1 - args.alpha) * content_loss
    loss.backward()
    opt.step()

    return style_loss.item(), content_loss.item()
