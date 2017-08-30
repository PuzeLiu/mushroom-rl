import numpy as np
import tensorflow as tf


class ConvNet:
    def __init__(self, n_actions, optimizer, name, folder_name,
                 width=84, height=84, history_length=4):
        self._name = name
        with tf.variable_scope(self._name):
            self._x = tf.placeholder(tf.float32,
                                     shape=[None,
                                            height,
                                            width,
                                            history_length],
                                     name='input')
            hidden_1 = tf.layers.conv2d(
                self._x, 32, 8, 4, activation=tf.nn.relu,
                kernel_initializer=tf.glorot_uniform_initializer(),
                bias_initializer=tf.glorot_uniform_initializer(),
                name='hidden_1'
            )
            hidden_2 = tf.layers.conv2d(
                hidden_1, 64, 4, 2, activation=tf.nn.relu,
                kernel_initializer=tf.glorot_uniform_initializer(),
                bias_initializer=tf.glorot_uniform_initializer(),
                name='hidden_2'
            )
            hidden_3 = tf.layers.conv2d(
                hidden_2, 64, 3, 1, activation=tf.nn.relu,
                kernel_initializer=tf.glorot_uniform_initializer(),
                bias_initializer=tf.glorot_uniform_initializer(),
                name='hidden_3'
            )
            flatten = tf.reshape(hidden_3, [-1, 7 * 7 * 64], name='flatten')
            features = tf.layers.dense(
                flatten, 512, activation=tf.nn.relu,
                kernel_initializer=tf.glorot_uniform_initializer(),
                bias_initializer=tf.glorot_uniform_initializer(),
                name='features'
            )
            self.q = tf.layers.dense(
                features, n_actions,
                kernel_initializer=tf.glorot_uniform_initializer(),
                bias_initializer=tf.glorot_uniform_initializer(),
                name='q'
            )

            self._target_q = tf.placeholder('float32', [None], name='target_q')
            self._action = tf.placeholder('uint8', [None], name='action')

            with tf.name_scope('gather'):
                action_one_hot = tf.one_hot(self._action, n_actions,
                                            name='action_one_hot')
                self._q_acted = tf.reduce_sum(self.q * action_one_hot,
                                              axis=1,
                                              name='q_acted')

            self._loss = tf.losses.huber_loss(self._target_q, self._q_acted)
            tf.summary.scalar('huber_loss', self._loss)
            tf.summary.scalar('average_q', tf.reduce_mean(self.q))

            if optimizer['name'] == 'rmspropgraves':
                opt = tf.train.RMSPropOptimizer(learning_rate=optimizer['lr'],
                                                decay=optimizer['decay'],
                                                centered=True)
            elif optimizer['name'] == 'rmsprop':
                opt = tf.train.RMSPropOptimizer(learning_rate=optimizer['lr'],
                                                decay=optimizer['decay'])
            elif optimizer['name'] == 'adam':
                opt = tf.train.AdamOptimizer()
            elif optimizer['name'] == 'adadelta':
                opt = tf.train.AdadeltaOptimizer()
            else:
                raise ValueError('Unavailable optimizer selected.')

            self._train_count = 0
            self._train_step = opt.minimize(loss=self._loss)

        self._session = tf.Session()
        self._session.run(tf.global_variables_initializer())

        self._merged = tf.summary.merge_all()
        self._train_writer = tf.summary.FileWriter(
            folder_name + '/' + self._name,
            graph=tf.get_default_graph()
        )

    def predict(self, x, **fit_params):
        if isinstance(x, list):
            return self._session.run(
                self._q_acted, feed_dict={self._x: x[0],
                                          self._action: x[1].ravel().astype(
                                              np.uint8)})
        return self._session.run(self.q, feed_dict={self._x: x})

    def train_on_batch(self, x, y, **fit_params):
        summaries, _ = self._session.run([self._merged, self._train_step],
                                         feed_dict={self._x: x[0],
                                         self._action: x[1].ravel().astype(
                                             np.uint8),
                                         self._target_q: y})
        self._train_writer.add_summary(summaries, self._train_count)

        self._train_count += 1

    def set_weights(self, weights):
        with tf.variable_scope(self._name):
            w = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,
                                  scope=self._name)
            assert len(w) == len(weights)

            for i in xrange(len(w)):
                self._session.run(tf.assign(w[i], weights[i]))

    def get_weights(self):
        w = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,
                              scope=self._name)

        return self._session.run(w)

    def save_weights(self):
        pass

    def load_weights(self):
        pass
