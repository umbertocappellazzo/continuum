import abc
from typing import List, Tuple, Union

import numpy as np
from torchvision import datasets as torchdata
from torchvision import transforms


class _ContinuumDataset(abc.ABC):

    def __init__(self, data_path: str = "", download: bool = True) -> None:
        self.data_path = data_path
        self.download = download

        if self.download:
            self._download()

    @abc.abstractmethod
    def get_data(self, train: bool) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        pass

    def _download(self):
        pass

    @property
    def class_order(self) -> Union[None, List[int]]:
        return None

    @property
    def need_class_remapping(self) -> bool:
        """Flag for method `class_remapping`."""
        return False

    def class_remapping(self, class_ids: np.ndarray) -> np.ndarray:
        """Optional class remapping.

        Used for example in PermutedMNIST, cf transformed.py;

        :param class_ids: Original class_ids.
        :return: A remapping of the class ids.
        """
        return class_ids

    @property
    def data_type(self) -> str:
        return "image_array"

    @property
    def transformations(self):
        return [transforms.ToTensor()]


class PyTorchDataset(_ContinuumDataset):
    """Continuum version of torchvision datasets.

    :param dataset_type: A Torchvision dataset, like MNIST or CIFAR100.
    """

    # TODO: some datasets have a different structure, like SVHN for ex. Handle it.
    def __init__(self, *args, dataset_type, train, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataset_type = dataset_type
        self.train = train

        self.dataset = self.dataset_type(self.data_path, download=self.download, train=self.train)

    @property
    def get_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        x, y = np.array(self.dataset.data), np.array(self.dataset.targets)
        return x, y, None


class InMemoryDataset(_ContinuumDataset):
    """Continuum dataset for in-memory data.

    :param x_train: Numpy array of images or paths to images for the train set.
    :param y_train: Targets for the train set.
    :param x_test: Numpy array of images or paths to images for the test set.
    :param y_test: Targets for the test set.
    :param data_type: Format of the data.
    :param t_train: Optional task ids for the train set.
    :param t_test: Optional task ids for the test set.
    """

    def __init__(
        self,
        x_: np.ndarray,
        y_: np.ndarray,
        data_type: str = "image_array",
        t_: Union[None, np.ndarray] = None,
        train='train',
        **kwargs
    ):

        self.train = train
        self.data = (x_, y_, t_)
        self._data_type = data_type
        super().__init__(**kwargs)

    def get_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return self.data

    @property
    def data_type(self) -> str:
        return self._data_type

    @data_type.setter
    def data_type(self, data_type: str) -> None:
        self._data_type = data_type


class ImageFolderDataset(_ContinuumDataset):
    """Continuum dataset for datasets with tree-like structure.

    :param train_folder: The folder of the train data.
    :param test_folder: The folder of the test data.
    :param download: Dummy parameter.
    """


    def __init__(self, folder: str, train: str, download: bool = True, **kwargs):
        super().__init__(download=download, **kwargs)

        self.folder = folder
        self.train = train

        if download:
            self._download()

        self.dataset = torchdata.ImageFolder(folder)

    @property
    def data_type(self) -> str:
        return "image_path"

    def _download(self):
        pass

    def get_data(self) -> Tuple[np.ndarray, np.ndarray, Union[None, np.ndarray]]:
        return self._format(self.dataset.imgs)


    @staticmethod
    def _format(raw_data: List[Tuple[str, int]]) -> Tuple[np.ndarray, np.ndarray, None]:
        x = np.empty(len(raw_data), dtype="S255")
        y = np.empty(len(raw_data), dtype=np.int16)

        for i, (path, target) in enumerate(raw_data):
            x[i] = path
            y[i] = target

        return x, y, None
