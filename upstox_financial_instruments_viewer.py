import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os

# Set page config
st.set_page_config(
    page_title="Financial Instruments JSON Viewer",
    page_icon="📊",
    layout="wide"
)


def load_json_file(file):
    """Load JSON data from uploaded file"""
    try:
        # Read the file content
        content = file.read()

        # Try to parse as JSON array first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            else:
                return [data]
        except json.JSONDecodeError:
            # If not a valid JSON array, try to parse line by line (JSONL format)
            lines = content.decode('utf-8').strip().split('\n')
            json_objects = []
            for line in lines:
                if line.strip():
                    try:
                        json_objects.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return json_objects
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return []


def convert_timestamp(timestamp):
    """Convert timestamp to readable date"""
    try:
        if pd.isna(timestamp) or timestamp == '' or timestamp == 0:
            return "N/A"
        # Convert to numeric if it's a string
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        # Convert from milliseconds to seconds
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid"


def format_currency(value):
    """Format currency values"""
    try:
        if pd.isna(value) or value == '' or value == 0:
            return "₹0.00"
        # Convert to numeric if it's a string
        if isinstance(value, str):
            value = float(value)
        return f"₹{value:,.2f}"
    except:
        return "N/A"


def main():
    st.title("📊 Financial Instruments JSON Viewer")
    st.markdown("Upload and analyze your financial instruments JSON data with interactive filters")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload JSON file",
        type=['json', 'jsonl'],
        help="Upload a JSON file containing financial instrument data"
    )

    if uploaded_file is not None:
        # Load data
        with st.spinner("Loading data..."):
            data = load_json_file(uploaded_file)

        if not data:
            st.error("No valid JSON data found in the file")
            return

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Display basic info
        st.subheader("📈 Dataset Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            unique_instruments = df['name'].nunique() if 'name' in df.columns and not df['name'].isna().all() else 0
            st.metric("Unique Instruments", unique_instruments)
        with col3:
            unique_exchanges = df['exchange'].nunique() if 'exchange' in df.columns and not df[
                'exchange'].isna().all() else 0
            st.metric("Exchanges", unique_exchanges)
        with col4:
            unique_types = df['instrument_type'].nunique() if 'instrument_type' in df.columns and not df[
                'instrument_type'].isna().all() else 0
            st.metric("Instrument Types", unique_types)

        # Sidebar filters
        st.sidebar.header("🔍 Filters")

        # Exchange filter
        if 'exchange' in df.columns:
            # Handle null and empty values
            exchange_values = df['exchange'].dropna().astype(str)
            exchange_values = exchange_values[exchange_values.str.strip() != '']
            if not exchange_values.empty:
                exchanges = ['All'] + sorted(exchange_values.unique().tolist())
                selected_exchange = st.sidebar.selectbox("Exchange", exchanges)
                if selected_exchange != 'All':
                    df = df[df['exchange'].astype(str).str.strip() == selected_exchange]

        # Instrument type filter
        if 'instrument_type' in df.columns:
            # Handle null and empty values
            instrument_values = df['instrument_type'].dropna().astype(str)
            instrument_values = instrument_values[instrument_values.str.strip() != '']
            if not instrument_values.empty:
                instrument_types = ['All'] + sorted(instrument_values.unique().tolist())
                selected_type = st.sidebar.selectbox("Instrument Type", instrument_types)
                if selected_type != 'All':
                    df = df[df['instrument_type'].astype(str).str.strip() == selected_type]

        # Segment filter
        if 'segment' in df.columns:
            # Handle null and empty values
            segment_values = df['segment'].dropna().astype(str)
            segment_values = segment_values[segment_values.str.strip() != '']
            if not segment_values.empty:
                segments = ['All'] + sorted(segment_values.unique().tolist())
                selected_segment = st.sidebar.selectbox("Segment", segments)
                if selected_segment != 'All':
                    df = df[df['segment'].astype(str).str.strip() == selected_segment]

        # Underlying type filter
        if 'underlying_type' in df.columns:
            # Handle null and empty values
            underlying_values = df['underlying_type'].dropna().astype(str)
            underlying_values = underlying_values[underlying_values.str.strip() != '']
            if not underlying_values.empty:
                underlying_types = ['All'] + sorted(underlying_values.unique().tolist())
                selected_underlying = st.sidebar.selectbox("Underlying Type", underlying_types)
                if selected_underlying != 'All':
                    df = df[df['underlying_type'].astype(str).str.strip() == selected_underlying]

        # Lot size filter
        if 'lot_size' in df.columns:
            # Handle null and non-numeric values
            lot_size_values = pd.to_numeric(df['lot_size'], errors='coerce').dropna()
            if not lot_size_values.empty and len(lot_size_values.unique()) > 1:
                min_lot = int(lot_size_values.min())
                max_lot = int(lot_size_values.max())
                if min_lot != max_lot:
                    lot_range = st.sidebar.slider(
                        "Lot Size Range",
                        min_value=min_lot,
                        max_value=max_lot,
                        value=(min_lot, max_lot)
                    )
                    df_lot_numeric = pd.to_numeric(df['lot_size'], errors='coerce')
                    df = df[
                        (df_lot_numeric >= lot_range[0]) & (df_lot_numeric <= lot_range[1]) & df_lot_numeric.notna()]

        # Strike price filter (for options)
        if 'strike_price' in df.columns:
            # Handle null and non-numeric values
            strike_price_values = pd.to_numeric(df['strike_price'], errors='coerce').dropna()
            if not strike_price_values.empty and len(strike_price_values.unique()) > 1:
                min_strike = float(strike_price_values.min())
                max_strike = float(strike_price_values.max())
                if min_strike != max_strike:
                    strike_range = st.sidebar.slider(
                        "Strike Price Range",
                        min_value=min_strike,
                        max_value=max_strike,
                        value=(min_strike, max_strike)
                    )
                    df_strike_numeric = pd.to_numeric(df['strike_price'], errors='coerce')
                    df = df[(df_strike_numeric >= strike_range[0]) & (
                                df_strike_numeric <= strike_range[1]) & df_strike_numeric.notna()]

        # Weekly filter
        if 'weekly' in df.columns:
            # Handle null and non-boolean values
            weekly_values = df['weekly'].dropna()
            if not weekly_values.empty:
                weekly_filter = st.sidebar.radio("Weekly Options", ['All', 'Weekly Only', 'Monthly Only'])
                if weekly_filter == 'Weekly Only':
                    df = df[df['weekly'] == True]
                elif weekly_filter == 'Monthly Only':
                    df = df[df['weekly'] == False]

        # Search filter
        search_term = st.sidebar.text_input("Search in Trading Symbol", "")
        if search_term and 'trading_symbol' in df.columns:
            # Handle null values in trading_symbol
            df = df[df['trading_symbol'].astype(str).str.contains(search_term, case=False, na=False)]

        # Display filtered results
        st.subheader(f"📋 Filtered Results ({len(df)} records)")

        if len(df) > 0:
            # Format display columns
            display_df = df.copy()

            # Format expiry timestamp
            if 'expiry' in display_df.columns:
                display_df['expiry_date'] = display_df['expiry'].apply(convert_timestamp)

            # Format strike price
            if 'strike_price' in display_df.columns:
                display_df['strike_price_formatted'] = display_df['strike_price'].apply(format_currency)

            # Select columns to display
            display_columns = []
            available_columns = [
                'instrument_key', 'name', 'trading_symbol', 'instrument_type', 'exchange', 'segment',
                'underlying_symbol', 'underlying_type', 'expiry_date', 'strike_price_formatted',
                'lot_size', 'minimum_lot', 'tick_size', 'exchange_token', 'weekly'
            ]

            for col in available_columns:
                if col in display_df.columns:
                    display_columns.append(col)

            # Display the table
            st.dataframe(
                display_df[display_columns],
                use_container_width=True,
                hide_index=True
            )

            # Download filtered data
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name=f"filtered_instruments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

            # Additional analysis
            st.subheader("📊 Quick Analysis")

            col1, col2 = st.columns(2)

            with col1:
                if 'instrument_type' in df.columns and not df['instrument_type'].isna().all():
                    st.subheader("Instrument Type Distribution")
                    type_counts = df['instrument_type'].value_counts()
                    if not type_counts.empty:
                        st.bar_chart(type_counts)
                    else:
                        st.info("No instrument type data available")
                else:
                    st.info("No instrument type data available")

            with col2:
                if 'lot_size' in df.columns:
                    # Handle lot size statistics with null values
                    lot_size_numeric = pd.to_numeric(df['lot_size'], errors='coerce').dropna()
                    if not lot_size_numeric.empty:
                        st.subheader("Lot Size Statistics")
                        st.write(f"**Average Lot Size:** {lot_size_numeric.mean():.0f}")
                        st.write(f"**Median Lot Size:** {lot_size_numeric.median():.0f}")
                        st.write(f"**Min Lot Size:** {lot_size_numeric.min():.0f}")
                        st.write(f"**Max Lot Size:** {lot_size_numeric.max():.0f}")
                    else:
                        st.info("No valid lot size data available")
                else:
                    st.info("No lot size data available")

            # Raw JSON view
            with st.expander("🔍 View Raw JSON Data (First 5 records)"):
                for i, record in enumerate(df.head(5).to_dict('records')):
                    st.json(record)
                    if i < 4:
                        st.divider()

        else:
            st.warning("No records match the current filters. Please adjust your filter criteria.")

    else:
        st.info("👆 Please upload a JSON file to get started")

        # Show sample data format
        st.subheader("📝 Expected Data Format")
        st.markdown("Your JSON file should contain financial instrument data in this format:")

        sample_data = {
            "weekly": False,
            "segment": "NSE_FO",
            "name": "071NSETEST",
            "exchange": "NSE",
            "expiry": 2111423399000,
            "instrument_type": "FUT",
            "underlying_symbol": "071NSETEST",
            "instrument_key": "NSE_FO|36702",
            "lot_size": 50,
            "freeze_quantity": 100000.0,
            "exchange_token": "36702",
            "minimum_lot": 50,
            "underlying_key": "NSE_EQ|DUMMYSAN011",
            "tick_size": 5.0,
            "underlying_type": "EQUITY",
            "trading_symbol": "071NSETEST FUT 27 NOV 36",
            "strike_price": 0.0
        }

        st.json(sample_data)


if __name__ == "__main__":
    main()