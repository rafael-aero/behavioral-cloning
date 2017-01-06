'''
Trains model for determining steering angle
'''
import json
import argparse
import numpy as np
from scipy import misc
from sklearn.model_selection import train_test_split

from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers import Convolution2D, ELU, Flatten, Dense, Dropout, Lambda
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img

np_dir = 'data/np_data/'
model_dir = 'models/'

'''
create a model to train the img data with
*why need time_len = 1?
'''
def make_model(time_len=1):
  #our data, 3 color channels, 160 by 320
  row, col, ch = 100, 320, 3
  start_shape = (row, col, ch)

  #set up sequential linear model (stacked on top of eachother)
  model = Sequential()

  #normalize pixels from 255 to be out of 1
  model.add(Lambda(lambda x: x / 127.5 - 1, input_shape=(start_shape), output_shape=(start_shape)))

  #convolutional 16, 8, 8 with subsample aka stridelength (4, 4), same padding means that it doesn't lose part on end? 
  model.add(Convolution2D(16, 8, 8, subsample=(4, 4), border_mode='same'))

  #ELU aka exponential linear unit(similar to RELU)
  model.add(ELU())
  model.add(Convolution2D(32, 5, 5, subsample=(2, 2), border_mode='same'))
  model.add(ELU())
  model.add(Convolution2D(64, 5, 5, subsample=(2, 2), border_mode='same'))

  #flatten and dropout .2
  model.add(Flatten())
  model.add(Dropout(.2))
  model.add(ELU())

  # dense (aka normal fully connected) -- outputs to size 512 (and doesnt matter input)
  model.add(Dense(512))
  model.add(Dropout(.5))
  model.add(ELU())

  #dense 1 -- outputs to 1 and then can 1-hot it?
  model.add(Dense(1)) 

  #compile model and return. setting loss to mean standard error because regression
  #no metrics
  adam = Adam(lr=0.0001)
  model.compile(optimizer=adam, loss='mse')

  return model

'''
create generator to create augmented images
'''
def myGenerator(X, y, batch_size, num_per_epoch):
  #preprocess images
  # print('X shape', X.shape)
  # print('y shape', y.shape)
  print('generator starting')
  # while True:
  for i in range(num_per_epoch):
    start, end = i * batch_size, (i + 1) * batch_size
    yield (X[start: end], y[start: end])

if __name__ == "__main__":
  # set up arg parser so that we can call python file with diff args
  parser = argparse.ArgumentParser(description='Model to train steering angles')
  #didn't include port options since dont need to run on server
  parser.add_argument('--batch', type=int, default=128, help='Batch size.')
  parser.add_argument('--epoch', type=int, default=2, help='Number of epochs.')
  #initially set to 10k but since I only have 7k photos, set to 7k
  parser.add_argument('--epochsize', type=int, default=512, help='How many images per epoch.')
  #confused by help--just skips validation when fit model right?
  parser.add_argument('--skipvalidate', dest='skipvalidate', action='store_true', help='?multiple path out.')
  parser.add_argument('--features', type=str, default=np_dir + 'cropped_udacity_images.npy', help='File where features .npy found.')
  parser.add_argument('--labels', type=str, default=np_dir + 'udacity_angles.npy', help='File where labels .npy found.')
  parser.add_argument('--destfile', type=str, default=model_dir + 'generator_4', help='File where model found')

  parser.set_defaults(skipvalidate=False)
  parser.set_defaults(loadweights=False)
  args = parser.parse_args()

  model = make_model()
  # print('model is', model)

  orig_features = np.load(args.features)
  print('orig features shape', orig_features.shape)
  # change channels to be in right place
  # orig_features = np.moveaxis(orig_features, 3, 1)
  # print('after axis move', orig_features.shape)

  orig_labels = np.load(args.labels)
  X_train, X_val, y_train, y_val = train_test_split(orig_features, orig_labels, test_size=.1, random_state=0)
  print('training model', args.destfile)
  print('X_train and y_train', X_train.shape, y_train.shape)

  print('X_val and y_val', X_val.shape, y_val.shape)
  #try to fit model normally without generator... 
  # model.fit(X_train, y_train, nb_epoch=args.epoch, batch_size=args.batch, shuffle=True, validation_data=(X_val, y_val))
  # train_datagen = ImageDataGenerator(horizontal_flip=True)
  # train_generator = myGenerator(X=X_train, y=y_train, batch_size=args.batch, num_per_epoch=args.epochsize)
  # print('train_datagen', train_datagen)

  # train_generator = train_datagen.flow(X_train, y_train, batch_size=args.batch)
  # validation_generator = train_datagen.flow(X_val, y_val, batch_size=args.batch)
  # print('train generator', train_generator)
  # train_datagen.fit(X_train)

  # X_batch, y_batch = train_datagen.flow(X_train, batch_size=32)
  # print('not one is', not_one)

  # train_generator = train_datagen.flow_from_directory(
  #   'data/udacity_IMG',
  #   target_size=(160, 320),
  #   batch_size=32,
  #   class_mode='sparse') #this doesnt seem like what we want todo

  # validation_generator = train_datagen.flow_from_directory(
  #   'data/bridge_recovery_IMG',
  #   target_size=(160, 320),
  #   batch_size=32,
  #   class_mode='sparse') 

  model.fit_generator(
    myGenerator(X=X_train, y=y_train, batch_size=args.batch, num_per_epoch=args.epochsize),
    nb_epoch=2, 
    samples_per_epoch=args.epochsize)
    # validation_data=validation_generator,
    # nb_val_samples=1024)

  print('model successfully fit...', model)

  #save the model
  model.save_weights(args.destfile + '.h5', True)
  # save weights as json
  with open(args.destfile + '.json', 'w') as outfile: 
    json.dump(model.to_json(), outfile)
