import sqlite3
import pandas as pd
import streamlit as st

conn = sqlite3.connect("inventory.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT UNIQUE, 
        quantity INTEGER, 
        price REAL
    )
    """
)
conn.commit()

st.title("Inventory System")
menu = st.sidebar.selectbox(
    "Navigation", ["View Inventory", "Add / Update Item", "Delete Item"]
)

if menu == "View Inventory":
    st.subheader("Current Stock")
    df = pd.read_sql("SELECT * FROM items", conn)
    if df.empty:
        st.info("No items in inventory yet.")
    else:
        st.dataframe(df, use_container_width=True)

elif menu == "Add / Update Item":
    st.subheader("Add or Update Stock")

    with st.form("inventory_form"):
        name = st.text_input("Item Name").strip().capitalize()
        quantity = st.number_input("Quantity", min_value=0, step=1)
        price = st.number_input("Price ($)", min_value=0.0, format="%.2f")
        submit = st.form_submit_button("Save Item")

        if submit:
            if name:
                cursor.execute(
                    """
                    INSERT INTO items(name, quantity, price)
                    VALUES (?, ?, ?)
                    ON CONFLICT(name)
                    DO UPDATE SET quantity = excluded.quantity, price = excluded.price
                    """,
                    (name, quantity, price),
                )
                conn.commit()
                st.success(f"Successfully saved: **{name}**!")
            else:
                st.error("Please enter an item name.")

elif menu == "Delete Item":
    st.subheader("Remove Item")
    df = pd.read_sql("SELECT name FROM items", conn)
    
    if df.empty:
        st.info("No items available to delete.")
    else:
        item_to_delete = st.selectbox("Select Item to Delete", df["name"])
        if st.button("Delete"):
            cursor.execute("DELETE FROM items WHERE name = ?", (item_to_delete,))
            conn.commit()
            st.success(f"Deleted **{item_to_delete}** from inventory.")
            st.rerun()