import pandas as pd
import psycopg2
import streamlit as st


def get_connection():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


# Initialize cloud database table
conn = get_connection()
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        quantity INTEGER,
        price REAL
    )
"""
)
conn.commit()
cursor.close()
conn.close()

st.title("Inventory System")

menu = st.sidebar.selectbox(
    "Navigation", ["Stock View", "Add & Restock", "Remove Item"]
)

if menu == "Stock View":
  st.subheader("Stock View")

  conn = get_connection()
  df = pd.read_sql("SELECT * FROM items", conn)
  conn.close()

  if df.empty:
    st.info("No items in inventory yet.")
  else:
    df["Total Price"] = df["quantity"] * df["price"]

    df["price"] = df["price"].map("₱{:,.2f}".format)
    df["Total Price"] = df["Total Price"].map("₱{:,.2f}".format)

    conn = get_connection()
    raw_df = pd.read_sql("SELECT quantity, price FROM items", conn)
    conn.close()

    total_stock_count = raw_df["quantity"].sum()
    total_inventory_value = (raw_df["quantity"] * raw_df["price"]).sum()

    col1, col2 = st.columns(2)
    col1.metric("Total Items", f"{total_stock_count:,}")
    col2.metric("Total Value", f"₱{total_inventory_value:,.2f}")

    st.markdown("---")
    st.dataframe(df, use_container_width=True)

elif menu == "Add & Restock":
  st.subheader("Add and Restock Items")

  with st.form("inventory_form"):
    name = st.text_input("Item Name").strip().capitalize()
    quantity_to_add = st.number_input(
        "Quantity", min_value=1, step=1, value=1
    )
    unit_price = st.number_input(
        "Unit Price (₱)", min_value=0.0, format="%.2f", value=0.0
    )
    submit = st.form_submit_button("Save Item")

    if submit:
      if name:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT quantity, price FROM items WHERE name = %s", (name,)
        )
        existing = cursor.fetchone()

        if existing:
          old_qty, old_price = existing
          new_qty = old_qty + quantity_to_add
          blended_price = ((old_qty * old_price) + (quantity_to_add * unit_price)) / new_qty

          cursor.execute(
              """
                        UPDATE items 
                        SET quantity = %s, price = %s
                        WHERE name = %s
                    """,
              (new_qty, blended_price, name),
          )
        else:
          cursor.execute(
              """
                        INSERT INTO items (name, quantity, price) 
                        VALUES (%s, %s, %s)
                    """,
              (name, quantity_to_add, unit_price),
          )

        conn.commit()
        cursor.close()
        conn.close()
        st.success(f"Successfully saved **{name}**!")
      else:
        st.error("Please enter an item name.")

elif menu == "Remove Item":
  st.subheader("Remove Item")
  conn = get_connection()
  df = pd.read_sql("SELECT name FROM items", conn)
  conn.close()

  if df.empty:
    st.info("No items available to remove.")
  else:
    item_to_delete = st.selectbox("Select Item", df["name"])
    if st.button("Delete"):
      conn = get_connection()
      cursor = conn.cursor()
      cursor.execute("DELETE FROM items WHERE name = %s", (item_to_delete,))
      conn.commit()
      cursor.close()
      conn.close()
      st.success(f"Removed **{item_to_delete}** from inventory.")
      st.rerun()
