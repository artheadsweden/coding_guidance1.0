"""
Mongo Doc Library
~~~~~~~~~~~~~~~~~~
A simple and easy to use library to access a MongoDB database.

Basic usage:
from mongo_doc import init_db, create_collection_class


# First initialize the database connection
init_db('mongodb://username:password@host:port')


# Create a collection class
User = create_collection_class('User', 'users')

# Create a user object using a dict
user = User(
    {
        'first_name': 'Alice',
        'last_name': 'Smith',
        'email': 'alice@email.com'
    })

# Create a user object using keyword arguments
user = User(
    first_name='Alice',
    last_name='Smith',
    email='alice@email.com'
)

# Save the object to the database
user.save()

# Search for all users with this first name and return the first hit
# or None if no documents are found
user = User.find(first_name='Alice').first_or_none()
if user:
    # Change the first name
    user.first_name = 'Bob'
    # and save it
    user.save()

:copyright: (c) 2023 by Joakim Wassberg.
:license: MIT License, see LICENSE for more details.
:version: 0.03
"""
from copy import copy
from typing import Union
import bson
import pymongo
from pymongo import MongoClient


# The __db object needs to be initialized before the library can be used
_db = None


# *******************
# Library exceptions
# *******************
class MongoException(Exception):
    """
    Base exception class
    """
    pass


class MongoDBConnectionError(MongoException):
    """
    Database initialization exceptions
    """
    pass


class MongoDBCollectionError(MongoException):
    """
    Collection exceptions
    """
    pass

class MongoFieldError(MongoException):
    """
    Field exceptions
    """
    pass


class ResultList(list):
    """
    Extends the list class with methods to retrieve the first or last value, or None if the list is empty
    This class is used as a return value for returned documents
    """
    def first_or_none(self):
        """
        Return the first value or None if list is empty
        :return: First list element or None
        """
        return self[0] if len(self) > 0 else None

    def last_or_none(self):
        """
       Return the last value or None if list is empty
       :return: Last list element or None
       """
        return self[-1] if len(self) > 0 else None


class Document(dict):
    """
    This class acts as the base class for collection classes. Each instance of the subclasses
    will represent a single document
    """
    collection = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        # If _id is not present we add the _id attribute
        if '_id' not in kwargs:
            self._id = None

        # Handle dict argument
        if len(args) > 0 and isinstance(args[0], dict):
            d = copy(args[0])
        else:
            d = copy(kwargs)

        # We need to check if there is an embedded document in this document.
        # If so, we will convert it into a dict
        for k, v in d.items():
            if isinstance(v, Document):
                d[k] = v.__dict__

        # Update the object
        self.__dict__.update(d)



    def __repr__(self):
        return '\n'.join(f'{k} = {v}' for k, v in self.__dict__.items())

    def _get_auto_id(self, sequence_name: str, increment: int=2) -> int:
        """
        Gives you an auto increment field in mongodb
        Works with a collection in your mongodb that needs to have the name
        counters.
        Each document needs to in the form:
        {
            "_id": "sequence_name",
            "sequence_value": 0
        }

        The _id needs to be a unique value per sequence you need to work with, defined as a string.
        The sequence_value is the starting value for the auto increment

        :param sequence_name: str - The name of the sequence to use (mathing the _id)
        :param increment: int - Optional, how much to increment the value each time. Default value is 2
        :return: int - The next value from the auto increment
        """
        if 'counters' not in _db.list_collection_names():
            raise MongoDBCollectionError('To use an auto increment field you need a collection called counters.')
        
        updated_record = _db.counters.find_one_and_update(
            filter = {"_id": sequence_name},
            upsert = True, 
            update = {"$inc": {"sequence_value": increment}},
            return_document=True
        )
        return updated_record['sequence_value']

    def save(self, auto_field=None, auto_key=None):
        """
        Saves the current object to the database
        :param auto_field: str | None, if using auto increment key, the name of the key field
        :param auto_key: str | None, name of the key used in counters collection for this auto increment 
        :return: The saved object
        """
        if self.collection is None:
            raise Exception('The collection does not exist')

        # If _id is None, this is a new document
        if self._id is None:
            res = self.collection.insert_one(self.__dict__)
            self._id = res.inserted_id
            return self
        else:
            # get the fields that have changed
            changed_fields = {}
            for key, value in self.__dict__.items():
                if key != '_id':
                    # compare with the value in the database
                    result = self.collection.find_one({'_id': self._id}, {key: 1})
                    if result and key in result and result[key] != value:
                        changed_fields[key] = value

            # if no fields have changed, return the document unchanged
            if not changed_fields:
                return self

            # update the document
            update_result = self.collection.update_one({'_id': self._id}, {'$set': changed_fields})
            if update_result.matched_count == 0:
                raise ValueError('Document with _id {} does not exist'.format(self._id))
            else:
                return self

    def delete_field(self, field):
        """
        Removes a field from this document
        :param field: str, the field to remove
        :return: None
        """
        self.collection.update_one({'_id': self._id}, {"$unset": {field: ""}})

    @classmethod
    def create_index(cls, keys, index_type=pymongo.ASCENDING, unique=False, name=None):
        """
        Creates an index on the specified keys
        :param keys: The keys to index on
        :param index_type: The index type, e.g. ASCENDING or DESCENDING
        :param unique: Whether the index should be unique
        :param name: The name of the index
        :return: None
        """
        index_name = name or '_'.join(keys) + '_' + index_type.lower()
        cls.collection.create_index([(key, index_type) for key in keys], name=index_name, unique=unique)

    @classmethod
    def get_by_id(cls, _id):
        """
        Get a document by its _id
        :param _id: str, the id of the document
        :return: The retrieved document or None
        """
        try:
            return cls(cls.collection.find_one({'_id': bson.ObjectId(_id)}))
        except bson.errors.InvalidId:
            return None

    @classmethod
    def insert_many(cls, items):
        """
        Inserts a list of dictionaries into the databse
        :param items: list of dict, items to insert
        :return: None
        """
        for item in items:
            cls(item).save()

    @classmethod
    def all(cls):
        """
        Retrieve all documents from the collection
        :return: ResultList of documents
        """
        return ResultList([cls(**item) for item in cls.collection.find({})])

    @classmethod
    def find(cls, **kwargs):
        """
        Find a document that matches the keywords
        :param kwargs: keyword arguments or dict to match
        :return: ResultList
        """
        if len(kwargs) == 1 and isinstance(kwargs.get(list(kwargs.keys())[0]), dict):
            d = copy(kwargs.get(list(kwargs.keys())[0]))
        else:
            d = copy(kwargs)
        return ResultList(cls(item) for item in cls.collection.find(d))

    @classmethod
    def find_in(cls, field, values):
        """
        Find a document that matches the keywords
        :param field: str, the field to search in
        :param values: list, the values to search for
        :return: ResultList
        """
        return ResultList(cls(item) for item in cls.collection.find({field: {"$in": values}}))

    @classmethod
    def delete(cls, **kwargs):
        """
        Delete the document that matches the keywords
        :param kwargs: keyword arguments or dict to match
        :return: None
        """
        if len(kwargs) == 1 and isinstance(kwargs.get(list(kwargs.keys())[0]), dict):
            d = copy(kwargs.get(list(kwargs.keys())[0]))
        else:
            d = copy(kwargs)
        cls.collection.delete_many(kwargs)

    @classmethod
    def document_count(cls):
        """
        Returns the total number of documents in the collection
        :return: int
        """
        return cls.collection.count_documents({})


# *******************
# Helper functions
# *******************

def create_collection_class(class_name: str, collection_name: Union[str, None] = None, schema: Dict[str, Any] = None):
    """
    Factory function for creating collection classes
    :param class_name: str, name of collection class
    :param collection_name: str or None, name of collection in database. If None, the class name will be used
    :param schema: dict or None, document schema. If None, no schema validation will be performed.
    :return: The newly created collection class
    """
    if collection_name is None:
        collection_name = class_name

    if _db is None:
        raise MongoDBConnectionError('init_db function must be called before creation of collection classes')

    # Define the collection class
    collection_class = type(class_name, (Document,), {'collection': _db[collection_name]})

    # Define the validate method if a schema is provided
    if schema is not None:
        def validate(self):
            for field_name, field_schema in schema.items():
                field_value = self.get(field_name)
                field_type = field_schema.get('type')
                field_required = field_schema.get('required', False)

                # Check that required fields are present
                if field_required and field_value is None:
                    raise ValueError(f"Required field '{field_name}' is missing")

                # Check that the field has the correct type
                if field_value is not None and not isinstance(field_value, field_type):
                    raise TypeError(f"Field '{field_name}' has invalid type. Expected {field_type}, got {type(field_value)}")

        # Add the validate method to the collection class
        collection_class.validate = validate

    return collection_class


def add_base_class(cls, base_class):
    """
    Helper function to add a base class to a collection class
    :param cls: The collection class
    :param base_class: The base class to add
    :return: None
    """
    cls.__bases__ = (base_class,) + cls.__bases__

def add_collection_method(cls, method):
    """
    Helper function to add methods to a collection class.
    Usage:
    def method(self):
        print(self.name)

    user = create_collection_class('User')
    add_collection_method(User, method)
    user.method()
    :param cls: The collection class
    :param method: The method to add to the class
    :return: None
    """
    setattr(cls, method.__name__, method)


def init_db(connection_str, database):
    """
    Function to initialize database connection. Must be called before any use of the library
    :param connection_str: str, the database connection string
    :param database: str, the name of the database to use
    :return: None
    """
    client = MongoClient(connection_str)
    if client is None:
        raise MongoDBConnectionError('Could not connect to database')
    global _db
    _db = client[database]

data = {
    'name': str,
    'age': int,
    'addresses': list(dict)
}