# Back-end for online store "Crochet & Knit"

This Python script sets up a Flask web application that serves as a backend for an online shopping platform. It connects to a MySQL database and provides various endpoints for handling products, customers, orders, and transactions. The application also includes functionality for uploading images and managing user accounts.

### Key Components

1. **Imports**:
   - The script imports necessary libraries such as `base64`, `json`, and `requests` for handling image uploads and JSON data.
   - `bcrypt` is used for hashing passwords securely.
   - `Flask`, `flask_mysqldb`, and `flask_cors` are used to create the web application, manage MySQL connections, and handle Cross-Origin Resource Sharing (CORS) respectively.
   - `dotenv` is used for loading environment variables from a `.env` file.

2. **Flask Application Setup**:
   - The Flask app is instantiated, and CORS is enabled to allow cross-origin requests.
   - Environment variables for the MySQL database configuration are loaded using `dotenv`.

3. **Database Configuration**:
   - MySQL database connection settings (host, user, password, database name) are set from environment variables.

4. **Routing**:
   - The route `catch_all` serves the `index.html` file from the specified directory when any path is requested. This is useful for serving a single-page application (SPA) that handles client-side routing.
   - The root route (`/`) returns a JSON response that describes available endpoints, including actions related to products, customers, orders, and transactions.

5. **Endpoints**:
   - The application provides various RESTful endpoints for:
     - Uploading product images.
     - Creating, retrieving, updating, and deleting products.
     - Managing customer accounts, including registration and login.
     - Updating customer details (email, password, phone).
     - Managing customer addresses.
     - Creating and retrieving orders.
     - Handling transactions and saving them in the database.

### Functionality

- **Image Upload**: The application supports image uploads for products using an external service (not shown in this snippet).
- **Product Management**: Users can create, update, retrieve, and delete products.
- **Customer Management**: Customers can register, log in, and manage their accounts and addresses.
- **Order Management**: The application allows customers to create orders and retrieve order details.
- **Transaction Management**: Transactions are saved in the database, enabling tracking of payment activities.

