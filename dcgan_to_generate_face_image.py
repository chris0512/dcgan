# -*- coding: utf-8 -*-
"""DCGAN to generate face image.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IN9PWXnt0sns73YLIm5sGSsRquI3SlSH

### DCGAN to generate face image
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import matplotlib.pyplot as plt
import os
import gdown
from zipfile import ZipFile
from tqdm import tqdm
import os

if not os.path.isdir("celeba_gan"):
  os.makedirs("celeba_gan")

  url = "https://drive.google.com/uc?id=1O7m1010EJjLE5QxLZiM9Fpjs7Oj6e684"
  output = "celeba_gan/data.zip"
  gdown.download(url, output, quiet=True)

with ZipFile("celeba_gan/data.zip", "r") as zipobj:
    zipobj.extractall("celeba_gan")

dataset = keras.preprocessing.image_dataset_from_directory(
    directory="celeba_gan", label_mode=None, image_size=(64, 64), batch_size=32,
    shuffle=True
).map(lambda x: x/255.0)

for x in dataset:
    plt.axis("off")
    plt.imshow((x.numpy() * 255).astype("int32")[0])
    break

"""Create the discriminator
* fake is 0
* real is 1
"""

discriminator = keras.Sequential(
    [
        keras.Input(shape=(64,64,3)),
        layers.Conv2D(64, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(0.2),
        layers.Conv2D(128, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(0.2),
        layers.Conv2D(128, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(0.2),
        layers.Flatten(),
        layers.Dropout(0.2),
        layers.Dense(1, activation="sigmoid"),
    ]
)

discriminator.summary()

""" Create the generator
 ##### It mirrors the discriminator, replacing Conv2D layers with Conv2DTranspose layers.



"""

latent_dim = 128
generator = keras.Sequential(
    [
        layers.Input(shape=(latent_dim,)),
        layers.Dense(8*8*128),
        layers.Reshape((8, 8, 128)),
        layers.Conv2DTranspose(128, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(0.2),
        layers.Conv2DTranspose(256, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(0.2),
        layers.Conv2DTranspose(512, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(0.2),
        layers.Conv2D(3, kernel_size=5, padding="same", activation="sigmoid"),
    ]
)
generator.summary()

"""setting hyperparameters"""

opt_gen = keras.optimizers.Adam(1e-4)
opt_disc = keras.optimizers.Adam(1e-4)
loss_fn = keras.losses.BinaryCrossentropy()

"""### train the model"""

os.makedirs("generated_images")

for epoch in range(10):
    for idx, real in enumerate(tqdm(dataset)):
        batch_size = real.shape[0]
        random_latent_vectors = tf.random.normal(shape=(batch_size, latent_dim))
        fake = generator(random_latent_vectors)

        if idx % 100 == 0:
            img = keras.preprocessing.image.array_to_img(fake[0])
            img.save(f"generated_images/generated_img{epoch}_{idx}_.png")

        ### Train Discriminator: max log(D(x)) + log(1 - D(G(z))
        with tf.GradientTape() as disc_tape:
            loss_disc_real = loss_fn(tf.ones((batch_size, 1)), discriminator(real))
            loss_disc_fake = loss_fn(tf.zeros(batch_size, 1), discriminator(fake))
            loss_disc = (loss_disc_real + loss_disc_fake)/2

        grads = disc_tape.gradient(loss_disc, discriminator.trainable_weights)
        opt_disc.apply_gradients(
            zip(grads, discriminator.trainable_weights)
        )

        ### Train Generator min log(1 - D(G(z)) <-> max log(D(G(z))
        with tf.GradientTape() as gen_tape:
            fake = generator(random_latent_vectors)
            output = discriminator(fake)
            loss_gen = loss_fn(tf.ones(batch_size, 1), output)

        grads = gen_tape.gradient(loss_gen, generator.trainable_weights)
        opt_gen.apply_gradients(
            zip(grads, generator.trainable_weights)
        )