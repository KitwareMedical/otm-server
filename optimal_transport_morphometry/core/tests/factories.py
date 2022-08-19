from django.contrib.auth.models import User
import factory.django

from optimal_transport_morphometry.core.models import (
    Atlas,
    Dataset,
    FeatureImage,
    Image,
    JacobianImage,
    PendingUpload,
    PreprocessingBatch,
    RegisteredImage,
    SegmentedImage,
    UploadBatch,
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.SelfAttribute('email')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class T1AtlasFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Atlas

    name = 'T1.nii.gz'
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='T1.nii.gz')


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    name = factory.Faker('word')
    description = factory.Faker('paragraph')
    owner = factory.SubFactory(UserFactory)


class UploadBatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UploadBatch

    dataset = factory.SubFactory(DatasetFactory)


class PendingUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PendingUpload

    name = factory.Faker('file_name', category='image')
    batch = factory.SubFactory(UploadBatchFactory)


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    name = factory.Faker('file_name', category='image')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    dataset = factory.SubFactory(DatasetFactory)


class PreprocessingBatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PreprocessingBatch

    dataset = factory.SubFactory(DatasetFactory)


class AbstractPreprocessedImageFactory(factory.django.DjangoModelFactory):
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    source_image = factory.SubFactory(ImageFactory)
    atlas = factory.SubFactory(T1AtlasFactory)
    preprocessing_batch = factory.SubFactory(PreprocessingBatchFactory)

    class Meta:
        abstract = True


class FeatureImageFactory(AbstractPreprocessedImageFactory):
    class Meta:
        model = FeatureImage

    downsample_factor = 3.0


class JacobianImageFactory(AbstractPreprocessedImageFactory):
    class Meta:
        model = JacobianImage


class RegisteredImageFactory(AbstractPreprocessedImageFactory):
    class Meta:
        model = RegisteredImage


class SegmentedImageFactory(AbstractPreprocessedImageFactory):
    class Meta:
        model = SegmentedImage
