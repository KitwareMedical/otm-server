from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm
import pytest

from optimal_transport_morphometry.core.models.dataset import Dataset

from . import fuzzy

# from optimal_transport_morphometry.core import batch_parser, models


@pytest.mark.django_db
def test_dataset_create(user, api_client):
    api_client.force_authenticate(user)

    r = api_client.post('/api/v1/datasets', {'name': 'test', 'description': 'asd'})
    assert r.status_code == 201
    assert r.json() == {
        'id': fuzzy.ID_RE,
        'name': 'test',
        'description': 'asd',
        'public': False,
        'preprocessing_complete': False,
        'analysis_complete': False,
    }


@pytest.mark.django_db
def test_dataset_create_unauthenticated(api_client):
    r = api_client.post('/api/v1/datasets', {'name': 'test', 'description': 'asd'})
    assert r.status_code == 400


@pytest.mark.django_db
def test_dataset_create_existing(user, api_client):
    # Create dataset with name
    Dataset.objects.create(name='test', owner=user)

    # Attempt to create dataset with the same name
    api_client.force_authenticate(user)
    r = api_client.post('/api/v1/datasets', {'name': 'test', 'description': 'asd'})
    assert r.status_code == 400


@pytest.mark.django_db
def test_dataset_create_existing_no_owner_conflict(user_factory, api_client):
    user1: User = user_factory()
    user2: User = user_factory()

    # Create dataset with name
    Dataset.objects.create(name='test', owner=user1)

    # Attempt to create dataset with the same name
    api_client.force_authenticate(user2)
    r = api_client.post('/api/v1/datasets', {'name': 'test', 'description': 'asd'})
    assert r.status_code == 201


@pytest.mark.django_db
def test_dataset_list(api_client, user, user_factory, dataset_factory):
    dataset: Dataset = dataset_factory(owner=user)
    user2: User = user_factory()
    user3: User = user_factory()

    # Assign collaborators
    assign_perm('collaborator', user2, dataset)

    # user is the dataset owner, user2 is a collaborator, user3 is neither
    # Assert user and user2 can see dataset
    api_client.force_authenticate(user)
    assert api_client.get('/api/v1/datasets').json()['count'] == 1
    api_client.force_authenticate(user2)
    assert api_client.get('/api/v1/datasets').json()['count'] == 1

    # Assert user3 can't see that dataset
    api_client.force_authenticate(user3)
    assert api_client.get('/api/v1/datasets').json()['count'] == 0


@pytest.mark.django_db
def test_dataset_list_public(api_client, user, user_factory, dataset_factory):
    dataset_factory()
    dataset_factory(public=True)

    # Assert user can only see the public dataset
    api_client.force_authenticate(user)
    assert api_client.get('/api/v1/datasets').json()['count'] == 1


@pytest.mark.django_db
def test_dataset_add_collaborator(api_client, user, user_factory, dataset_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(name='test', owner=user)
    user2: User = user_factory()
    r = api_client.put(
        f'/api/v1/datasets/{dataset.pk}/collaborators',
        [{'username': user2.username}],
    )
    assert r.status_code == 204
    assert user2.has_perm('collaborator', dataset)

    r = api_client.get(f'/api/v1/datasets/{dataset.pk}/collaborators')
    assert r.status_code == 200
    assert r.json() == [
        {
            'id': user2.pk,
            'username': user2.username,
        }
    ]


@pytest.mark.django_db
def test_dataset_add_collaborator_unauthenticated(api_client, user, user_factory, dataset_factory):
    dataset: Dataset = dataset_factory(name='test', owner=user)
    user2: User = user_factory()
    r = api_client.put(
        f'/api/v1/datasets/{dataset.pk}/collaborators',
        [{'username': user2.username}],
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_dataset_add_collaborator_not_owner(api_client, user, user_factory, dataset_factory):
    user2: User = user_factory()
    api_client.force_authenticate(user2)

    dataset: Dataset = dataset_factory(name='test', owner=user)
    r = api_client.put(
        f'/api/v1/datasets/{dataset.pk}/collaborators',
        [{'username': user2.username}],
    )
    assert r.status_code == 400
    assert r.json() == ['Only dataset owner can set collaborators.']


@pytest.mark.django_db
def test_dataset_add_collaborator_is_owner(api_client, user, dataset_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(name='test', owner=user)
    r = api_client.put(
        f'/api/v1/datasets/{dataset.pk}/collaborators',
        [{'username': user.username}],
    )
    assert r.status_code == 400
    assert r.json() == [f"Cannot assign dataset owner '{user.username}' as collaborator."]


@pytest.mark.django_db
def test_dataset_add_collaborator_invalid_user(api_client, user, user_factory, dataset_factory):
    api_client.force_authenticate(user)
    dataset: Dataset = dataset_factory(name='test', owner=user)

    # Assert missing username is caught
    r = api_client.put(f'/api/v1/datasets/{dataset.pk}/collaborators', [{}])
    assert r.status_code == 400
    assert r.json() == [{'username': ['This field is required.']}]

    # Assert non-existant username is caught
    r = api_client.put(
        f'/api/v1/datasets/{dataset.pk}/collaborators',
        [{'username': 'notarealuser'}],
    )
    assert r.status_code == 400
    assert r.json() == {'username': 'User with username notarealuser not found.'}


@pytest.mark.django_db
def test_dataset_get_collaborators(api_client, user, user_factory, dataset_factory):
    api_client.force_authenticate(user)
    dataset: Dataset = dataset_factory(name='test', owner=user)

    # Assert missing username is caught
    r = api_client.put(f'/api/v1/datasets/{dataset.pk}/collaborators', [{}])
    assert r.status_code == 400
    assert r.json() == [{'username': ['This field is required.']}]

    # Assert non-existant username is caught
    r = api_client.put(
        f'/api/v1/datasets/{dataset.pk}/collaborators',
        [{'username': 'notarealuser'}],
    )
    assert r.status_code == 400
    assert r.json() == {'username': 'User with username notarealuser not found.'}
