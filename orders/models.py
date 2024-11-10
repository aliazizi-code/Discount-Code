from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from products.models import Product, ProductCategory


def calculate_discount_price(original_price, discount_percentage):
    """
        Calculates the discounted price based on the original price and discount percentage.

        Parameters:
        original_price (float or str): The initial price before discount.
        discount_percentage (float or str): The percentage of discount to apply.

        Returns:
        Decimal: The price after applying the discount.

        Raises:
        ValueError: If the original price or discount percentage is non-positive.
        """
    try:
        # Convert inputs to Decimal for precise calculations
        original_price = Decimal(original_price)
        discount_percentage = Decimal(discount_percentage)

        # Check if price and discount percentage are positive
        if original_price <= 0 or discount_percentage <= 0:
            raise ValueError("Price and discount percentage must be non-negative.")

        discount_amount = original_price * (discount_percentage / 100)  # Calculate the discount amount
        discounted_price = original_price - discount_amount     # Compute the final discounted price

        return Decimal(discounted_price)
    except ValueError as e:
        print(f'Error: {e}')    # Print error message for value issues
    except Exception as e:
        print('An unexpected error occurred:', e)   # Handle unexpected errors


# Function to compute the discount amount based on the discount code and total amount
def compute_discount_amount(discount_code, total):
    # Check if minimum purchase requirement is met, if specified
    if discount_code.min_purchase is None or (
            discount_code.min_purchase is not None and discount_code.min_purchase <= total):

        # Discount by fixed price
        if discount_code.off_price is not None and discount_code.off_per is None:
            total -= discount_code.off_price
            return total

        # Discount by percentage
        if discount_code.off_price is None and discount_code.off_per is not None:
            total = calculate_discount_price(total, discount_code.off_per)
            return total

        # Discount by both fixed price and percentage
        if discount_code.off_price is not None and discount_code.off_per is not None:
            decreased_amount = total - calculate_discount_price(total, discount_code.off_per)

            # Apply the fixed discount if it does not exceed the reduced amount
            if decreased_amount > discount_code.off_price:
                total -= discount_code.off_price
            else:
                total = calculate_discount_price(total, discount_code.off_per)

    return total


class DiscountCode(models.Model):
    code = models.CharField(max_length=30, unique=True, null=False, blank=False)  # Unique discount code
    off_per = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True,
                                  blank=True)  # Percentage off
    off_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True,
                                    blank=True)  # Fixed price off
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
                                       null=True, blank=True)  # Minimum purchase amount
    is_active = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    is_first = models.BooleanField(default=False)  # Indicates if the discount code is for first-time users
    exp_date = models.DateField(null=True, blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)

    # Method to check if the discount code is valid
    def is_valid(self):
        # Discount code must be active and not deleted
        if not self.is_active or self.is_delete:
            return False

        # Ensure there is remaining quantity if specified
        if self.quantity is not None and self.quantity <= 0:
            return False

        # At least one discount type must be specified
        if self.off_price is None and self.off_per is None:
            return False

        # Check if the discount code is expired
        if self.exp_date and self.exp_date < timezone.now().date():
            return False

        return True

    def str(self):
        return self.code


# Model representing an order
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    is_payment = models.BooleanField(default=False)  # Indicates if the order has been paid
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, null=True, blank=True)

    # Method to calculate the total price of the order
    def get_total_price_order(self):
        total_amount = Decimal(0)

        # Iterate through all order details and accumulate their total prices
        for order_detail in self.orderdetail_set.all():
            total_amount += order_detail.get_total_price_detail()

        # Check if there is a valid discount code
        if self.discount_code is not None and self.discount_code.is_valid():
            # Ensure no specific product or category restrictions for the discount code
            if self.discount_code.category is None and self.discount_code.product is None:
                # Check if the discount is applicable for first-time users
                if (self.discount_code.is_first and not self.user.order_set.filter(
                        is_payment=True).exists()) or not self.discount_code.is_first:
                    # Compute the total amount after applying the discount
                    total_amount = compute_discount_amount(self.discount_code, total_amount)

        return round(total_amount, 2)

    def str(self):
        return str(self.user)


# Model representing the details of an order
class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, blank=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, blank=False)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
                                      null=True, blank=True)  # Final price after discounts
    count = models.IntegerField(validators=[MinValueValidator(1)], null=False, blank=False)

    # Method to calculate the total price of this order detail
    def get_total_price_detail(self):
        base_price = Decimal(self.count * self.product.price)  # Calculate base price based on count and product price
        discount_code = self.order.discount_code  # Get the associated discount code

        # Helper functions to check discount applicability
        def is_category_match(discount_code, product):
            is_category_matched = discount_code.category == product.category
            is_product_available = discount_code.product is None
            return is_category_matched and is_product_available

        def is_product_match(discount_code, product):
            product_matched = discount_code.product == product
            is_category_available = discount_code.category is None
            return product_matched and is_category_available

        def is_category_and_product_match(discount_code, product):
            is_category_matched = discount_code.category in {product.category, product.category.parent}
            is_product_matched = discount_code.product == product
            return is_category_matched and is_product_matched

        def is_discount_applicable(discount_code, product):
            return (
                    is_category_match(discount_code, product) or
                    is_product_match(discount_code, product) or
                    is_category_and_product_match(discount_code, product)
            )

        # Check for a valid discount code
        if discount_code is None or not discount_code.is_valid():
            return round(base_price, 2)

        # Handle the case for first-time orders
        if discount_code.is_first and self.order.user.order_set.filter(is_payment=True):
            return round(base_price, 2)

        # Check if the discount can be applied
        valid_discount = is_discount_applicable(discount_code, self.product)

        if valid_discount:
            return round(compute_discount_amount(discount_code, base_price), 2)

        return round(base_price, 2)

    def str(self):
        return str(self.order)
