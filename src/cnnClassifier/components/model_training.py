import os
import urllib.request as request
import shutil
from zipfile import ZipFile
import tensorflow as tf
import time
from pathlib import Path
from cnnClassifier.entity.config_entity import TrainingConfig
from cnnClassifier import logger


class Training:
    def __init__(self, config: TrainingConfig):
        self.config = config

    
    def get_base_model(self):
        self.model = tf.keras.models.load_model(
            self.config.updated_base_model_path
        )

    def train_valid_generator(self):

        datagenerator_kwargs = dict(
            rescale = 1./255,
            validation_split=0.20
        )

        dataflow_kwargs = dict(
            target_size=self.config.params_image_size[:-1],
            batch_size=self.config.params_batch_size,
            interpolation="bilinear"
        )

        valid_datagenerator = tf.keras.preprocessing.image.ImageDataGenerator(
            **datagenerator_kwargs
        )

        self.valid_generator = valid_datagenerator.flow_from_directory(
            directory=self.config.training_data,
            subset="validation",
            shuffle=False,
            **dataflow_kwargs
        )

        if self.config.params_is_augmentation:
            train_datagenerator = tf.keras.preprocessing.image.ImageDataGenerator(
                rotation_range=40,
                horizontal_flip=True,
                width_shift_range=0.2,
                height_shift_range=0.2,
                shear_range=0.2,
                zoom_range=0.2,
                **datagenerator_kwargs
            )
        else:
            train_datagenerator = valid_datagenerator

        self.train_generator = train_datagenerator.flow_from_directory(
            directory=self.config.training_data,
            subset="training",
            shuffle=True,
            **dataflow_kwargs
        )



    def save_model(self,path: Path, model: tf.keras.Model, epoch_path: Path):
        model.save(path)
        last_epoch =  str(self.config.params_epochs)
        f =open(epoch_path, "w+")
        f.write(last_epoch)
        f.close()

    def copy_model(self, from_path : Path, to_path : Path):
        shutil.copy(from_path, to_path)
        

    
    def train(self):
        self.steps_per_epoch = self.train_generator.samples // self.train_generator.batch_size
        self.validation_steps = self.valid_generator.samples // self.valid_generator.batch_size

        if os.path.isfile("artifacts/training/model.h5") == True:
            self.model = tf.keras.models.load_model("artifacts/training/model.h5")


        if os.path.getsize("epochs.txt") != 0 and os.path.isfile("artifacts/training/model.h5") == True:
            f = open("epochs.txt", "r")
            initial_epoch = int(f.read())
        else:
            initial_epoch = 0



        if  self.config.params_epochs > initial_epoch:
            logger.info(f"***** training started from epoch   {initial_epoch+1} ******")

            self.model.fit(
                self.train_generator,
                epochs=self.config.params_epochs,
                steps_per_epoch=self.steps_per_epoch,
                validation_steps=self.validation_steps,
                validation_data=self.valid_generator,
                initial_epoch = initial_epoch
            )

            self.save_model(
                path=self.config.trained_model_path,
                model=self.model,
                epoch_path= Path("epochs.txt")

            ) 
            
            self.copy_model(
                from_path = Path('artifacts/training/model.h5'), 
                to_path = Path('model/model.h5') 
            ) 

        else:
            logger.info(f"***** Number of epochs {self.config.params_epochs} is less than or equal to initial epoch   {initial_epoch}  make it greater than {initial_epoch} epoch to start the training.******")
