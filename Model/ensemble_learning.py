import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
from sklearn.metrics import confusion_matrix
import time
from datetime import timedelta
import math
import os
import prettytensor as pt
from Utils import next_batch
from Utils import load_pkl_data
from Utils import load_pd_data


# def generate_train_validate_set():
#    return

def build_model(image_size, num_channels, num_classes):
    x = tf.placeholder(tf.float32, shape=[None, image_size * image_size], name="x")
    x_image = tf.reshape(x, [-1, image_size, image_size, num_channels])
    y_true = tf.placeholder(tf.float32, shape=[None, 8], name="y_true")
    y_true_cls = tf.argmax(y_true, axis=1)

    # create wrapper tensor
    x_pretty = pt.wrap(x_image)
    with pt.defaults_scope(activation_fn=tf.nn.elu):
        y_pred, loss = x_pretty. \
            conv2d(5, 16, name='layer_conv1'). \
            max_pool(2, 2). \
            conv2d(3, 32, name='layer_conv2'). \
            max_pool(2, 2). \
            conv2d(3, 64, name= 'layer_conv3'). \
            max_pool(2, 2).\
            flatten(). \
            fully_connected(128, name='layer_fc1'). \
            fully_connected(32, name= 'layer_fc2'). \
            softmax_classifier(num_classes=num_classes, labels=y_true)
    optimizer = tf.train.AdamOptimizer(1e-4).minimize(loss)
    y_pred_cls = tf.argmax(y_pred, axis=1)
    prediction_accuracy = tf.reduce_mean(tf.cast(tf.equal(y_true_cls, y_pred_cls)
                                                 , tf.float32))

    return optimizer, x, y_true, prediction_accuracy


# early stop if last_improvement = 0 for last EARLY_STOP_ITERATIONS iterations
def run_model(sess, num_iterations, optimizer, prediction_accuracy, x, y_true, x_train, y_train, train_batch_size=128,
              early_stop_iterations=500):
    global total_iterations
    global best_val_accuracy
    global last_improvement
    sess.run(tf.global_variables_initializer())
    start_time = time.time()
    for i in range(num_iterations):
        x_batch, y_batch = next_batch(x_train, y_train, train_batch_size)
        feed_dict = {x: x_batch, y_true: y_batch}
        sess.run(optimizer, feed_dict=feed_dict)
        if i % 10 == 0:
            cur_accuracy = sess.run(prediction_accuracy, feed_dict=feed_dict)
            print ("Iteration: ", i + 1, " Accuracy: ", cur_accuracy)
    end_time = time.time()
    time_elapsed = end_time - start_time
    print("Total time used: ", time_elapsed)

def ensemble(num_networks, num_iterations, optimizer, accuracy, x, y_true, x_train, y_train, batch_size = 128):
    sess = tf.Session()
    # Define model Saver
    saver = tf.train.Saver()
    save_dir = './model/'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    #save_path = os.path.join(save_dir, 'best_validation')
    for i in range(num_networks):
        print ('Network ', i, ': ')
        train_batch, test_batch = next_batch(x_train, y_train, batch_size)
        run_model(sess, num_iterations, optimizer, accuracy, x, y_true, x_train, y_train, batch_size)
        saver.save(sess=sess, save_path=save_dir + 'network '+ str(i))



if __name__ == '__main__':
    print('Loading Data ...')
    total_iterations = 0
    best_val_accuracy = 0.0
    last_improvement = 0.0
    img_size = 96
    num_channels = 1
    num_classes = 8
    num_iterations = 50
    batch_size = 128
    #early_stop_iterations = 500
    num_networks = 5

    x_train, y_train, _, _ = load_pd_data('../Data/pixel_nocomplex.pd')
    op, x, y_true, accuracy = build_model(img_size, num_channels,  num_classes)
    #run_model(num_iterations, op, accuracy, x, y_true, x_train, y_train, batch_size)
    ensemble(num_networks, num_iterations, op, accuracy, x, y_true, x_train, y_train, batch_size)


