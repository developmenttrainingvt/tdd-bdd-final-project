######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch
from flask import abort
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory


# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_get_product(self):
        """It should Read a Product"""
        test_product = self._create_products()[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_product = response.get_json()

        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_get_product_not_found(self):
        """It should Response with a Not Found error when the product is not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """It should Update a Product"""
        test_product = self._create_products()[0]
        data = test_product.serialize()
        data["description"] = "Test description"
        logging.debug("Test Product: %s", data)
        response = self.client.put(f"{BASE_URL}/{test_product.id}", json=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{BASE_URL}/{test_product.id}")

        product = response.get_json()
        self.assertEqual(product["name"], data["name"])
        self.assertEqual(product["description"], data["description"])
        self.assertEqual(Decimal(product["price"]), Decimal(data["price"]))
        self.assertEqual(product["available"], data["available"])
        self.assertEqual(product["category"], data["category"])

    def test_update_product_not_found(self):
        """It should fail when trying to update a not existing product"""
        test_product = self._create_products()[0]
        data = test_product.serialize()
        data["description"] = "Test description"
        logging.debug("Test Product: %s", data)
        response = self.client.put(f"{BASE_URL}/0", json=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_invalid_method(self):
        """It should fail when trying to update a product using invalid method"""
        test_product = self._create_products()[0]
        data = test_product.serialize()
        logging.debug("Test Product: %s", data)
        response = self.client.patch(f"{BASE_URL}/{test_product.id}", json=data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_product(self):
        """It should Delete Products"""
        products = self._create_products(5)
        self.assertEqual(self.get_product_count(), 5)

        test_product = products[0]

        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.get_product_count(), 4)

    def test_delete_product_not_found(self):
        """It should fail when trying to delete a not found product"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("service.routes.Product.find")
    def test_internal_error_handling(self, find_mock):
        """It should handle unexpected errors properly"""
        find_mock.side_effect = lambda id: abort(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "",
        )
        test_product = self._create_products()[0]
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_product_list(self):
        """It should Get a list of Products"""
        products = self._create_products(5)
        self.assertEqual(self.get_product_count(), 5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.get_json()
        self.assertEqual(len(products), 5)

    def test_list_products_by_name(self):
        """It should filter products by name"""
        products = self._create_products(5)
        test_name = products[0].name
        count_by_name = [product.name for product in products].count(test_name)

        response = self.client.get(f"{BASE_URL}?name={test_name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listed_products = response.get_json()
        self.assertEqual(len(listed_products), count_by_name)

        for product in listed_products:
            self.assertEqual(product["name"], test_name)

    def test_list_products_by_category(self):
        """It should filter products by category"""
        products = self._create_products(5)
        test_category = products[0].category.name
        count_by_category = [product.category.name for product in products].count(test_category)

        response = self.client.get(f"{BASE_URL}?category={test_category}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listed_products = response.get_json()
        self.assertEqual(len(listed_products), count_by_category)

        for product in listed_products:
            self.assertEqual(product["category"], test_category)

    def test_list_products_by_availability(self):
        """It should filter products by availability"""
        products = self._create_products(10)
        test_availablity = products[0].available
        count_by_availablity = [product.available for product in products].count(test_availablity)

        response = self.client.get(f"{BASE_URL}?available={test_availablity}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listed_products = response.get_json()
        self.assertEqual(len(listed_products), count_by_availablity)

        for product in listed_products:
            self.assertEqual(product["available"], test_availablity)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
