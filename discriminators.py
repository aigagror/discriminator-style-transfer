import tensorflow as tf

from style_content import FLAGS


class FirstMomentLoss(tf.keras.losses.Loss):
    def call(self, y_true, y_pred):
        tf.debugging.assert_rank(y_true, 3)
        tf.debugging.assert_rank(y_pred, 3)

        mu1 = tf.reduce_mean(y_true, axis=1)
        mu2 = tf.reduce_mean(y_pred, axis=1)

        std1 = tf.math.reduce_std(y_true, axis=1)
        std2 = tf.math.reduce_std(y_pred, axis=1)

        loss = (mu1 - mu2) ** 2 + (std1 - std2) ** 2

        return loss


class ThirdMomentLoss(tf.keras.losses.Loss):
    def call(self, y_true, y_pred):
        feats1, feats2 = y_true, y_pred
        tf.debugging.assert_rank(feats1, 3)
        tf.debugging.assert_rank(feats2, 3)

        mu1 = tf.reduce_mean(feats1, axis=1, keepdims=True)
        mu2 = tf.reduce_mean(feats2, axis=1, keepdims=True)

        std1 = tf.math.reduce_std(feats1, axis=1, keepdims=True)
        std2 = tf.math.reduce_std(feats2, axis=1, keepdims=True)

        skew1 = tf.reduce_mean((feats1 - mu1) ** 3, keepdims=True) / (std1 + 1e-5) ** 3
        skew2 = tf.reduce_mean((feats2 - mu2) ** 3, keepdims=True) / (std2 + 1e-5) ** 3

        loss = (mu1 - mu2) ** 2 + (std1 - std2) ** 2 + tf.abs(skew1 - skew2) * 1e-20

        return loss


class GramianLoss(tf.keras.losses.Loss):
    def call(self, y_true, y_pred):
        tf.debugging.assert_rank(y_true, 3)
        tf.debugging.assert_rank(y_pred, 3)

        num_locs = tf.cast(tf.shape(y_true)[1], y_true.dtype)

        gram_true = tf.linalg.einsum('bnc,bnd->bcd', y_true, y_true) / num_locs
        gram_pred = tf.linalg.einsum('bnc,bnd->bcd', y_pred, y_pred) / num_locs

        return (gram_true - gram_pred) ** 2


def make_discriminator():
    if FLAGS.disc == 'm1':
        return FirstMomentLoss()
    elif FLAGS.disc == 'gram':
        return GramianLoss()
    elif FLAGS.disc == 'm3':
        return ThirdMomentLoss()
    else:
        raise ValueError(f'unknown discriminator: {FLAGS.disc}')
