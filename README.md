# JakoB

#### Description:
## JakoB E-commerce Website  
A personal e-commerce project built as a final project for the CS50 course.

---

## Project Overview

### Frontend:
* HTML  
* CSS  
* JavaScript (mention any libraries or frameworks if used)

### Backend:
* Python (Flask)

### Database:
* SQLite3 (CS50 Library)

### Other:
* Stripe (for payment processing)  
* SendGrid (for emails)

---

## Key Features
* **User Authentication:** Secure registration and login system.  
* **Product Catalog:** Displays products with images, descriptions, and pricing.  
* **Shopping Cart:** Add/remove items and view cart with calculated totals.  
* **Stripe Checkout:** Integrated secure payment processing.  
* **Contact Form:** User inquiries handled via SendGrid integration.  
* **User Profile:** Basic user information and shipping address management.  

---

## Technical Description

The e-commerce website consists of 14 HTML pages, 1 CSS file, and 1 JavaScript file. These frontend components interact with a Python (Flask) backend, a SQLite3 database, and the Stripe API for payment processing. The static folder contains image assets used throughout the site.

---

## Frontend Structure

* **index.html:** Serves as the base template for the website. It contains core HTML structure, the navigation bar (Home, Shop, About Us, Contact, Cart, Profile), and the footer. Authentication logic controls navigation visibility.

* **home.html:** Main landing page for authenticated users with a call-to-action directing users to the shop.

* **signup.html:** Registration form with validation and password hashing on the backend.

* **login.html:** User authentication page validating credentials from the database.

* **shop.html:** Displays available products with images, names, and prices.

* **shoping1.html, shoping2.html, shoping3.html:** Product detail pages with size, color, quantity selection, and add-to-cart functionality.

* **aboutus.html:** Brand story, mission, and vision.

* **contact.html:** Contact form integrated with SendGrid for email delivery.

* **cart.html:** Displays cart items with total calculation and checkout options.

* **myaccount.html:** User profile and shipping address management.

* **success.html, cancel.html:** Stripe payment result pages.

---

## Backend Structure

The database (`users.db`) uses SQLite3 via the CS50 Library.

The **users** table stores user information such as email, name, password hash, and address details.

The **products** table stores product information including names, descriptions, prices, images, categories, and stock levels.

The **cart** table stores items added to the cart including product ID, size, color, quantity, and price.

The **shipping** table stores shipping information such as country, city, zip code, and address.

---

## Application Logic (app.py)

The application is built using Flask and includes product browsing, cart management, and Stripe payment integration.

It supports user registration, login, and a contact form using SendGrid for email functionality.

The database is managed using SQLite and the CS50 library.

Sensitive data such as API keys are stored in environment variables.

---

## helpers.py

The `helpers.py` file contains a `login_required` decorator from CS50 Week 9.

It ensures users must be logged in to access protected routes. If not logged in, users are redirected to the login page.
