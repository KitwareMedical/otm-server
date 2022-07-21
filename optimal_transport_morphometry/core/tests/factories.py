from django.contrib.auth.models import User
import factory.django

from optimal_transport_morphometry.core.models import (
    Atlas,
    Dataset,
    FeatureImage,
    Image,
    JacobianImage,
    RegisteredImage,
    SegmentedImage,
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

    name = 'T1.nii'
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='T1.nii')


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    name = factory.Faker('word')
    description = factory.Faker('paragraph')
    owner = factory.SubFactory(UserFactory)


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    name = factory.Faker('file_name', category='image')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    dataset = factory.SubFactory(DatasetFactory)


class FeatureImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FeatureImage

    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    source_image = factory.SubFactory(ImageFactory)
    atlas = factory.SubFactory(T1AtlasFactory)
    downsample_factor = 3.0


class JacobianImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JacobianImage

    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    source_image = factory.SubFactory(ImageFactory)
    atlas = factory.SubFactory(T1AtlasFactory)


class RegisteredImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegisteredImage

    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    source_image = factory.SubFactory(ImageFactory)
    atlas = factory.SubFactory(T1AtlasFactory)


class SegmentedImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SegmentedImage

    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    source_image = factory.SubFactory(ImageFactory)
    atlas = factory.SubFactory(T1AtlasFactory)
