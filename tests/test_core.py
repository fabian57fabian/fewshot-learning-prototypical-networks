import os
import uuid
import shutil
import numpy as np
from PIL import Image
from unittest import TestCase
from src.core import get_allowed_base_datasets_names, meta_train, meta_test, learn, predict


class TestCore(TestCase):

    def setUp(self) -> None:
        self.model_to_use = "../models/omniglot_28_5shot.pt"
        self.model_outputs = 64

        # Create centroids for learn()
        self.path_learn = "test_dataset_test_to_load"
        if os.path.exists(self.path_learn):
            shutil.rmtree(self.path_learn)
        os.mkdir(self.path_learn)
        self.centroids_images = 5
        self.classes_num = 3
        self.classes_of_learn = []
        for i in range(self.classes_num):
            class_name = str(i)
            cl_path = os.path.join(self.path_learn, class_name)
            os.mkdir(cl_path)
            self.classes_of_learn.append(class_name)
            for i_image in range(self.centroids_images):
                im_path = os.path.join(cl_path, str(uuid.uuid4()) + ".jpg")
                Image.new('RGB', (28, 28)).save(im_path)

        # Create data for meta_train()
        self.base_datasets_meta_train = "datasets"
        if os.path.exists(self.base_datasets_meta_train):
            shutil.rmtree(self.base_datasets_meta_train)
        os.mkdir(self.base_datasets_meta_train)
        custom_dts_name = "custom_1"
        self.datasets_to_meta_learn = [custom_dts_name, "mini_imagenet", "omniglot", "flowers102"]
        self.channels_to_meta_learn = [3, 3, 1, 3]
        self.meta_train_images = 10
        self.meta_train_classes_num = 5
        for dataset, channels in zip(self.datasets_to_meta_learn, self.channels_to_meta_learn):
            path_meta_train = os.path.join(self.base_datasets_meta_train, dataset)
            os.mkdir(path_meta_train)
            for phase in ["train", "test", "val"]:
                path_phase = os.path.join(path_meta_train, phase)
                os.mkdir(path_phase)
                for i in range(self.meta_train_classes_num):
                    class_name = str(i)
                    cl_path = os.path.join(path_phase, class_name)
                    os.mkdir(cl_path)
                    for i_image in range(self.meta_train_images):
                        im_path = os.path.join(cl_path, str(uuid.uuid4()) + ".jpg")
                        img = Image.new('RGB', (28, 28))
                        if channels == 1:
                            img = img.convert('L')
                        img.save(im_path)
        # custom dataset should be path to a dataset to train
        self.datasets_to_meta_learn[0] = os.path.join(self.base_datasets_meta_train, custom_dts_name)

        # Create centroids data for predict()
        self.path_load_centroids = "test_dataset_centroids"
        if os.path.exists(self.path_load_centroids): shutil.rmtree(self.path_load_centroids)
        os.mkdir(self.path_load_centroids)
        self.classes_files = 3
        self.classes_of_predict = []
        for i in range(self.classes_files):
            class_name = str(i)
            cl_path = os.path.join(self.path_load_centroids, class_name + ".npy")
            centroids = np.random.randint(0, 10, self.model_outputs) / 10
            np.save(cl_path, centroids)
            self.classes_of_predict.append(class_name)
        # Create images for predict()
        self.path_images_predict = "images_predict"
        if os.path.exists(self.path_images_predict):
            shutil.rmtree(self.path_images_predict)
        os.mkdir(self.path_images_predict)
        self.num_images_predict = 2
        for i in range(self.num_images_predict):
            im_path = os.path.join(self.path_images_predict, str(uuid.uuid4()) + ".jpg")
            Image.new('RGB', (28, 28)).save(im_path)

    def tearDown(self) -> None:
        if os.path.exists(self.base_datasets_meta_train):
            shutil.rmtree(self.base_datasets_meta_train)

        if os.path.exists(self.path_load_centroids):
            shutil.rmtree(self.path_load_centroids)

        if os.path.exists(self.path_images_predict):
            shutil.rmtree(self.path_images_predict)

        if os.path.exists(self.path_learn):
            shutil.rmtree(self.path_learn)

        if os.path.exists("runs"):
            shutil.rmtree("runs")

    def test_get_allowed_base_datasets_names(self):
        ad = get_allowed_base_datasets_names()
        assert type(ad) is list
        assert len(ad) == 3

    def test_meta_train(self):
        for i, (dts, ch) in enumerate(zip(self.datasets_to_meta_learn, self.channels_to_meta_learn)):
            dataset = dts
            epochs = 2
            gpu = False
            adam_lr = 0.1
            train_num_class = self.meta_train_classes_num - 1
            val_num_class = int(self.meta_train_classes_num / 2)
            usable_supp_query = self.meta_train_images - 2
            train_num_query = int(usable_supp_query * .4)
            number_support = int(usable_supp_query * .6)
            episodes_per_epoch = 10
            opt_step_size = 20
            opt_gamma = .5
            distance_function ="euclidean"
            image_size = 16
            image_ch = ch
            save_each = 1
            eval_each = 2

            meta_train(dataset, epochs, gpu, adam_lr,
                       train_num_class, val_num_class, train_num_query, number_support,
                       episodes_per_epoch, opt_step_size, opt_gamma, distance_function,
                       image_size, image_ch, save_each, eval_each)
            assert os.path.exists("runs")
            path_run = f"runs/train_{i}"
            assert os.path.exists(path_run)
            files = list(os.listdir(path_run))
            assert "model_best.pt" in files
            for i in range(epochs + 1):
                assert f"model_{i}.pt" in files
            assert "config.yaml" in files

    def test_meta_test(self):
        dataset_to_test_index = 1

        model = self.model_to_use
        episodes_per_epoch = 10

        dataset = self.datasets_to_meta_learn[dataset_to_test_index]
        gpu = False
        test_num_class = int(self.meta_train_classes_num / 2)
        usable_supp_query = self.meta_train_images - 2
        test_num_query = int(usable_supp_query * .4)
        number_support = int(usable_supp_query * .6)
        distance_function = "euclidean"
        image_size = 16
        image_ch = self.channels_to_meta_learn[dataset_to_test_index]
        acc = meta_test(model, episodes_per_epoch, dataset, gpu,
                        test_num_query, test_num_class, number_support,
                        distance_function, image_size, image_ch)
        assert acc is not None

    def test_learn(self):
        model = self.model_to_use
        data = self.path_learn
        image_size = 28
        image_ch = 3
        gpu = False
        learn(model, data, image_size, image_ch, gpu)
        assert os.path.exists("runs")
        path_centroids = "runs/centroids_0"
        assert os.path.exists(path_centroids)
        for file_npy in os.listdir(path_centroids):
            assert file_npy.endswith("npy")
            class_name = file_npy[:-4]
            assert class_name in self.classes_of_learn
            path = os.path.join(path_centroids, file_npy)
            np_file = np.load(path)
            assert np_file.shape[0] == self.model_outputs

    def test_predict(self):
        model = self.model_to_use
        centroids = self.path_load_centroids
        path = self.path_images_predict
        images = [path] if os.path.isfile(path) else [os.path.join(path, f) for f in os.listdir(path)]
        image_size = 28
        batch_size = 1
        gpu = False
        res = predict(model, centroids, images, image_size, batch_size, gpu)
        assert len(res) == len(images)
        for (cls, classification), im_path in zip(res, images):
            assert classification in self.classes_of_predict
            assert cls == im_path