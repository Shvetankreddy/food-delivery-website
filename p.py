import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth
from firebase_admin import initialize_app

# Initialize Firebase Admin SDK with the service account key file
cred = credentials.Certificate("food-website-48e34-870213080673.json")

# Check if the app is already initialized
try:
    firebase_admin.get_app()
except ValueError as e:
    # If not initialized, then initialize it with the credentials and storage bucket
    initialize_app(cred, {'storageBucket': 'streamlitchat-a40f7.appspot.com'})

# Define Firestore database
db = firestore.client()

# Define the main function for your food delivery website
def main():
    st.title(":green[Food] Delivery Website ")

    # Check if user is logged in
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''
    if "signedout" not in st.session_state:
        st.session_state["signedout"] = False
    if 'signout' not in st.session_state:
        st.session_state['signout'] = False

    # Function to handle login
    def login(email, password):
        st.write(f"Attempting login with email: {email}")
        if email.strip() == "" or password.strip() == "":
            st.warning("Please enter both email and password.")
            return

        try:
            user = auth.get_user_by_email(email)
            if user:
                # Authenticate user using Firebase Authentication client SDK
                # Here you might want to implement additional security measures, such as verifying the password
                st.write('Login Successful')
                st.session_state.useremail = user.email
                st.session_state.signedout = True
                st.session_state.signout = True
        except Exception as e:
            st.error(f'Login Failed: {e}')

    # Function to handle signup
    def signup(email, password):
        st.write(f"Attempting signup with email: {email}")
        if email.strip() == "" or password.strip() == "":
            st.warning("Please enter both email and password.")
            return

        try:
            user = auth.create_user(
                email=email,
                password=password
            )
            if user:
                st.write('Signup Successful')
                st.session_state.useremail = user.email
                st.session_state.signedout = True
                st.session_state.signout = True
        except Exception as e:
            st.error(f'Signup Failed: {e}')

    # Function to handle logout
    def sign_out():
        st.session_state.signout = False
        st.session_state.signedout = False
        st.session_state.useremail = ''

    # Function to fetch and display orders for the admin
    def display_orders():
        st.header("Orders Placed")
        orders_ref = db.collection("orders")
        query = orders_ref.where("status", "==", "Pending")
        orders = query.stream()

        for order in orders:
            order_data = order.to_dict()
            st.write(f"User: {order_data['user_email']}, Total Cost: ${order_data['total_cost']}, Status: {order_data['status']}")

            # Display items ordered by the user
            st.write("Items Ordered:")
            for item in order_data['items_ordered']:
                st.write(f"- {item['quantity']}x {item['item']}")

            if st.button(f"Accept Order {order.id}"):
                # Update order status to "Accepted"
                order_ref = orders_ref.document(order.id)
                order_ref.update({"status": "Accepted"})
                st.success("Order Accepted!")
                # Notify user
                notify_user(order_data['user_email'])

            if st.button(f"Decline Order {order.id}"):
                # Update order status to "Declined"
                order_ref = orders_ref.document(order.id)
                order_ref.update({"status": "Declined"})
                st.success("Order Declined!")

    # Function to notify user about order acceptance
    def notify_user(user_email):
        # Implement logic to send notification (e.g., email, SMS)
        st.write(f"Notification sent to {user_email}")

    # Function to handle adding items to the cart
    def add_to_cart(item, quantity):
        if 'cart' not in st.session_state:
            st.session_state.cart = []

        # Check if the item is already in the cart
        item_index = next((index for (index, d) in enumerate(st.session_state.cart) if d["item"] == item), None)
        if item_index is not None:
            st.session_state.cart[item_index]["quantity"] += quantity
        else:
            st.session_state.cart.append({"item": item, "quantity": quantity})

    # Function to display the cart sidebar
    def display_cart():
        st.sidebar.title("Cart")

        if 'cart' in st.session_state and len(st.session_state.cart) > 0:
            st.sidebar.subheader("Your Items:")
            total_cost = 0.0
            for item in st.session_state.cart:
                total_cost += item['quantity'] * menu_items[item['item']]
                st.sidebar.write(f"{item['quantity']}x {item['item']}")
            st.sidebar.write(f"Total Cost: ${total_cost}")
            if st.sidebar.button("Place Order"):
                # Save order to Firestore
                order_data = {
                    "user_email": st.session_state.useremail,
                    "items_ordered": st.session_state.cart,
                    "total_cost": total_cost,
                    "status": "Pending"
                }
                db.collection("orders").add(order_data)
                st.sidebar.success("Order Placed Successfully!")
                # Clear the cart after placing the order
                st.session_state.cart = []
        else:
            st.sidebar.write("Your cart is empty.")

    # Display login/signup options
    if not st.session_state["signedout"]:
        choice = st.selectbox('Login/Signup', ['Login', 'Sign up'])
        if choice == "Login":
            email = st.text_input('Email Address')
            password = st.text_input('Password', type='password')
            if st.button('Login'):
                login(email, password)
        else:
            email = st.text_input('Email Address')
            password = st.text_input('Password', type='password')
            if st.button('Create my account'):
                signup(email, password)

    # Display user information and logout button if logged in
    if st.session_state.signout:
        st.text('Email: ' + st.session_state.useremail)
        st.button('Sign out', on_click=sign_out)

        # Food Menu and Ordering Section (Only display for non-admin users)
        if st.session_state.useremail != "admin@gmail.com":
            st.header("Food Menu")
            menu_items = {
                "Burger": 5.99,
                "Pizza": 8.99,
                "Salad": 6.49,
                "Fries": 2.99
            }

            selected_items = []
            total_cost = 0.0

            for item, cost in menu_items.items():
                quantity = st.number_input(f"{item} (${cost})", min_value=0, max_value=10)
                if quantity > 0:
                    selected_items.append((item, quantity))
                    total_cost += cost * quantity

            if st.button("Add Items to Cart"):
                for item, quantity in selected_items:
                    add_to_cart(item, quantity)

            st.write(f"Total Cost: ${total_cost}")

    # Admin Page
    if st.session_state.useremail == "admin@gmail.com":
        display_orders()

    # Display the cart sidebar if user is logged in and not an admin
    if st.session_state.signout and st.session_state.useremail != "admin@gmail.com":
        display_cart()

# Run the main function when the script is executed
if __name__ == "__main__":
    main()