# Discount Code Mini Project 🎟

This mini project provides a discount code system designed for e-commerce websites. It allows users to apply various types of discount codes during their purchases. 

## Features 🌟

- 🛍 First Purchase Discount: Discount codes can be applied specifically for first-time buyers.
- 📅 Expiration Date: Each discount code can have an expiration date.
- 🔒 Limited Usage: Control the number of times a discount code can be used.
- 🏷 Product-Specific Discounts: Apply discounts only to specific products.
- 📦 Category-Specific Discounts: Apply discounts to specific product categories.
- 📊 Percentage Discounts: Use discount codes with percentage values ranging from 0% to 100%.
- 💵 Fixed Amount Discounts: Apply a fixed discount amount (e.g., $100 off).
- 📏 Minimum Purchase Requirement: Set a minimum purchase amount for the discount to be valid.
- 🎯 Capped Discounts: Define discounts such as 50% off up to a maximum of $10.

## Usage

You can run this project using Docker. Follow these commands to build and run the application:

`bash
docker build -t discountcode:1.0.0 . && docker run -d -p 8000:8000 discountcode:1.0.0
