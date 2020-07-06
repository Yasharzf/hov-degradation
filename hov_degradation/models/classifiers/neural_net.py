"""Script for feed forward classification model"""

import tensorflow as tf

tf.compat.v1.disable_eager_execution()


class FeedForwardClassifier:
    """Feed forward neural networks for classification.

    Attributes
    ----------
    # TODO
    """

    def __init__(self,
                 xs,
                 ys,
                 xs_test,
                 ys_test,
                 epochs,
                 batch_size,
                 learning_rate,
                 target_ckpt):

        self.xs = xs
        self.ys = ys
        self.xs_test = xs_test
        self.ys_test = ys_test
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.target_ckpt = target_ckpt

        self.model = None

    def build_model(self):
        """
        """
        tf.compat.v1.reset_default_graph()
        self.model = None  # TODO yf

    def compute_loss_mse(self):
        return tf.reduce_mean(tf.square(self.outputs - self.labels_ph))

    def train(self):
        """
        """
        # TODO yf
        pass
