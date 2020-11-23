from django.contrib.auth.models import User
import factory.django

from optimal_transport_morphometry.core.models import Dataset, Image


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.SelfAttribute('email')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    name = factory.Faker('word')
    description = factory.Faker('paragraph')


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    name = factory.Faker('file_name', category='image')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    owner = factory.SubFactory(UserFactory)
