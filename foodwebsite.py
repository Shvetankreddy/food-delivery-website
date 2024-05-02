import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import requests

#firebase initialized or not 
if not firebase_admin._apps:
    cred = credentials.Certificate("food-website-48e34-870213080673.json")
    firebase_admin.initialize_app(cred)
# admin credentials
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "123456"

def main():
    st.title(":violet[FOOD] DELIVERY WEBSITE")

    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''

    
    # Initialize Firestore database connection
    db = firestore.client()

    def is_admin(email):
        return email ==ADMIN_EMAIL

  
    def admin_login(email, password):
        return email == ADMIN_EMAIL and password == ADMIN_PASSWORD

    def display_admin_page():
        st.header("Admin Page")
       
    def user_login(email, password):
        #sign in function
        pass
    def sign_up_with_cred(email, password, username=None, return_secure_token=True):
        #sign up function
        try:
            rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
            details_user = {
                "email": email,
                "password": password,
                "returnSecureToken": return_secure_token
            }
            if username:
                details_user["displayName"] = username 
            details_user = json.dumps(details_user)
            r = requests.post(rest_api_url, params={"key": "AIzaSyApr-etDzcGcsVcmaw7R7rPxx3A09as7uw"}, data=details_user)
            try:
                return r.json()['email']
            except:
                st.warning(r.json())
        except Exception as e:
            st.warning(f'Signup failed: {e}')

    def sign_in_with_cred(email=None, password=None, return_secure_token=True):
        #sign in function
        rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

        try:
            details_user = {
                "returnSecureToken": return_secure_token
            }
            if email:
                details_user["email"] = email
            if password:
                details_user["password"] = password
            details_user = json.dumps(details_user)
            print('details_user sigin',details_user)
            r = requests.post(rest_api_url, params={"key": "AIzaSyApr-etDzcGcsVcmaw7R7rPxx3A09as7uw"}, data=details_user)
            try:
                data = r.json()
                user_info = {
                    'email': data['email'],
                    'username': data.get('displayName')  
                }
                return user_info
            except:
                st.warning(data)
        except Exception as e:
            st.warning(f'Signin failed: {e}')

    

    def f(): 
        #  login function
        try:
            userinfo = sign_in_with_cred(st.session_state.email_input,st.session_state.password_input)
            st.session_state.username = userinfo['username']
            st.session_state.useremail = userinfo['email']
            st.session_state.signedout = True
            st.session_state.signout = True    
  
        except: 
            st.warning('Login Failed')

    def t():
        # sign out function
        st.session_state.signout = False
        st.session_state.signedout = False   
        st.session_state.username = ''

#if you forget password(recovery)
    def forget():
        email = st.text_input('Email (Forget Password)')
        if st.button('Send Reset Link'):
            success, message = reset_password(email)
            if success:
                st.success("Password reset email sent successfully.")
            else:
                st.warning(f"Password reset failed: {message}") 

    if "signedout" not in st.session_state:
        st.session_state["signedout"] = False
    if 'signout' not in st.session_state:
        st.session_state['signout'] = False    

    if not st.session_state["signedout"]: 
        choice = st.selectbox('Login/Signup',['Login','Sign up'])
        email = st.text_input('Email Address (Login/Signup)')
        password = st.text_input('Password (Login/Signup)',type='password')
        st.session_state.email_input = email
        st.session_state.password_input = password

        if choice == 'Sign up':
            username = st.text_input("Enter your unique username (Sign up)")
            if st.button('Create my account'):
                user = sign_up_with_cred(email=email,password=password,username=username)
                st.success('Account created successfully!')
                st.markdown('Please Login using your email and password')
                
        else:
            st.button('Login', on_click=f)
            

    if st.session_state.signout:
        st.text('Name '+st.session_state.username)
        st.text('Email id: '+st.session_state.useremail)
        st.button('Sign out', on_click=t) 
    # User Authentication 
    if st.session_state.useremail == '':
        email = st.text_input('Email Address (Admin)')
        password = st.text_input('Password (Admin)', type='password')

        if st.button('Login (Admin)'):
            if admin_login(email, password):
                st.session_state.useremail = email
                st.success('Admin Login Successful!')
            else:
                # Check if it's a user login
                user_info = user_login(email, password)
                if user_info:
                    st.session_state.username = user_info['username']
                    st.session_state.useremail = user_info['email']
                    st.success('User Login Successful!')
                else:
                    st.error('Login Failed. Please check your credentials.')

    #admin page 
    if is_admin(st.session_state['useremail']):
        display_admin_page()
    else:
        #else user content
        pass

    def display_orders_admin():
        st.header("Orders Placed by Users")
        orders_ref = db.collection("orders")
        orders = orders_ref.stream()

        for order in orders:
            order_data = order.to_dict()
            st.write(f"Order ID: {order.id}")

            # Ensure 'user_email', 'total_cost', and 'status' keys exist before accessing
            if 'user_email' in order_data and 'total_cost' in order_data and 'status' in order_data:
                st.write(
                    f"User: {order_data['user_email']}, Total Cost: ₹{order_data['total_cost']}, Status: {order_data['status']}")

                # Display items ordered by the user
                st.write("Items Ordered:")
                for item in order_data.get('items_ordered', []):  
                    st.write(f"- {item.get('quantity', 0)}x {item.get('item', 'Unknown')}")  

                if order_data['status'] == "Pending":
                    if st.button(f"Accept Order {order.id}"):
                        # Update order status to "Accepted"
                        order_ref = orders_ref.document(order.id)
                        order_ref.update({"status": "Accepted"})
                        st.success("Order Accepted!")
                       
                        notify_user_and_update_status(order_data['user_email'], order.id, "Accepted")

                    if st.button(f"Decline Order {order.id}"):
                        # Update order status to "Declined"
                        order_ref = orders_ref.document(order.id)
                        order_ref.update({"status": "Declined"})
                        st.success("Order Declined!")
                        
                        notify_user_and_update_status(order_data['user_email'], order.id, "Declined")
                else:
                    st.warning("Order data is incomplete or missing.")
    # Function to notify user about order status
    def notify_user_and_update_status(user_email, order_id, status):
      
        st.write(f"Notification sent to {user_email}")
        

    # Function to handle adding items to the cart
    def add_to_cart(item, quantity):
        if 'cart' not in st.session_state:
            st.session_state['cart'] = []

        # Check if the item is already in the cart
        item_index = next((index for (index, d) in enumerate(st.session_state['cart']) if d["item"] == item), None)
        if item_index is not None:
            st.session_state['cart'][item_index]["quantity"] += quantity
        else:
            st.session_state['cart'].append({"item": item, "quantity": quantity})


    def display_cart():  
        st.sidebar.title("Cart")
        menu_items = {
            "Chicken Biryani": 320,
            "Veg fried rice": 185,
            "Alfaham mandi": 275,
            "Fries": 60,
            "Egg fried rice" :120,
            "Ice cream":65,
            "Sandwich":90,
            "Cake":500,
            "Noodles":95
        
        }
        
        if st.session_state['useremail'] != "admin@gmail.com":
            st.header("Food Menu")
            selected_items = []
            total_cost = 0.0
            for item, cost in menu_items.items():
                quantity = st.number_input(f"{item} (₹{cost})", min_value=0, max_value=10)
                if quantity > 0:
                    selected_items.append((item, quantity))
                    total_cost += cost * quantity

            if st.button("Add Items to Cart"):
                for item, quantity in selected_items:
                    add_to_cart(item, quantity)
            st.write(f"Total Cost: ₹{total_cost}")


        if 'cart' in st.session_state and len(st.session_state['cart']) > 0:
            st.sidebar.subheader("Your Items:")
            total_cost = 0.0
            for item in st.session_state['cart']:
                total_cost += item['quantity'] * menu_items[item['item']]
                st.sidebar.write(f"{item['quantity']}x {item['item']}")
            st.sidebar.write(f"Total Cost: ₹{total_cost}")

            if st.sidebar.button("Place Order"):
               
                order_data = {
                    "user_email": st.session_state['useremail'],
                    "items_ordered": st.session_state['cart'],
                    "total_cost": total_cost,
                    "status": "Pending"
                }
                db = firestore.client()
                db.collection("orders").add(order_data)
                st.sidebar.success("Order Placed Successfully!")        
                # Clears cart
                st.session_state['cart'] = []
        else:
            st.sidebar.write("Your cart is empty.")
        
    # Admin Page
    if st.session_state['useremail'] == ADMIN_EMAIL:
       
        display_orders_admin()

    # cart shows up only if user logs in 
    if st.session_state['signout'] and st.session_state['useremail'] != "admin@gmail.com":
        display_cart()
    else:
        pass
    
   
main()
