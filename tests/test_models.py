# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a product from the database"""
        product = ProductFactory()
        product.id = None
        product.create()

        self.assertIsNotNone(product.id)

        found_product = Product.find(product.id)

        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(Decimal(found_product.price), product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a product to the database"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        update_data = {
            "name": "Test name",
            "description": "Test description",
            "price": 1234.50,
            "avaliable": True,
            "category": Category.HOUSEWARES
        }
        product_to_update = Product.find(product.id)
        for name, value in update_data.items():
            setattr(product_to_update, name, value)

        product_to_update.update()

        found_product = Product.find(product_to_update.id)

        for name, value in update_data.items():
            self.assertEqual(getattr(found_product, name), value)

    def test_delete_a_product(self):
        """It should Delete a product from the database"""
        product = ProductFactory()
        product.id = None
        product.create()

        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)

        product.delete()

        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_list_all_products(self):
        """It should List all products from the database"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        products = ProductFactory.create_batch(5)
        for product in products:
            product.id = None
            product.create()

        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_a_product_by_name(self):
        """It should Find a product by name from the database"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.id = None
            product.create()

        products = Product.all()
        self.assertEqual(len(products), 5)
        name = products[0].name
        count_by_name = [product.name for product in products].count(name)

        found_products = Product.find_by_name(name)
        self.assertEqual(found_products.count(), count_by_name)

        for product in found_products:
            self.assertEqual(product.name, name)

    def test_find_a_product_by_availability(self):
        """It should Find a product by availability from the database"""
        products = ProductFactory.create_batch(10)

        for product in products:
            product.id = None
            product.create()

        products = Product.all()
        self.assertEqual(len(products), 10)
        availability = products[0].available
        count_by_availability = [product.available for product in products].count(availability)

        found_products = Product.find_by_availability(availability)
        self.assertEqual(found_products.count(), count_by_availability)

        for product in found_products:
            self.assertEqual(product.available, availability)

    def test_find_a_product_by_category(self):
        """It should Find a product by category from the database"""
        products = ProductFactory.create_batch(10)

        for product in products:
            product.id = None
            product.create()

        products = Product.all()
        self.assertEqual(len(products), 10)
        category = products[0].category
        count_by_category = [product.category for product in products].count(category)

        found_products = Product.find_by_category(category)
        self.assertEqual(found_products.count(), count_by_category)

        for product in found_products:
            self.assertEqual(product.category, category)
