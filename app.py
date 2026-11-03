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

 

st.title("📦 Smart Inventory System") 

 

menu = st.sidebar.selectbox( 

    "Navigation", ["View Inventory", "Add / Update Item", "Delete Item"] 

) 

 

if menu == "View Inventory": 

  st.subheader("Current Stock & Portfolio Value") 

 

  df = pd.read_sql("SELECT * FROM items", conn) 

 

  if df.empty: 

    st.info("No items in inventory yet.") 

  else: 

    df["Total Price"] = df["quantity"] * df["price"] 

 

    df["price"] = df["price"].map("${:,.2f}".format) 

    df["Total Price"] = df["Total Price"].map("${:,.2f}".format) 

 

    raw_df = pd.read_sql("SELECT quantity, price FROM items", conn) 

    total_stock_count = raw_df["quantity"].sum() 

    total_inventory_value = (raw_df["quantity"] * raw_df["price"]).sum() 

 

    col1, col2 = st.columns(2) 

    col1.metric("Total Items in Stock", f"{total_stock_count:,}") 

    col2.metric("Total Inventory Value", f"${total_inventory_value:,.2f}") 

 

    st.markdown("---") 

    st.dataframe(df, use_container_width=True) 

 

elif menu == "Add / Update Item": 

  st.subheader("Add Stock (Calculates Average Price)") 

 

  with st.form("inventory_form"): 

    name = st.text_input("Item Name").strip().capitalize() 

    quantity_to_add = st.number_input( 

        "Quantity to Add", min_value=1, step=1, value=1 

    ) 

    unit_price = st.number_input( 

        "Unit Price ($)", min_value=0.0, format="%.2f", value=0.0 

    ) 

    submit = st.form_submit_button("Add to Stock") 

 

    if submit: 

      if name: 

        cursor.execute( 

            "SELECT quantity, price FROM items WHERE name = ?", (name,) 

        ) 

        existing = cursor.fetchone() 

 

        if existing: 

          old_qty, old_price = existing 

          new_qty = old_qty + quantity_to_add 

          blended_price = ((old_qty * old_price) + (quantity_to_add * unit_price)) / new_qty 

 

          cursor.execute( 

              """ 

                        UPDATE items  

                        SET quantity = ?, price = ? 

                        WHERE name = ? 

                    """, 

              (new_qty, blended_price, name), 

          ) 

        else: 

          cursor.execute( 

              """ 

                        INSERT INTO items (name, quantity, price)  

                        VALUES (?, ?, ?) 

                    """, 

              (name, quantity_to_add, unit_price), 

          ) 

 

        conn.commit() 

        st.success(f"Successfully updated stock for **{name}**!") 

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
