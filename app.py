import streamlit as st
try:
    import time
    import os
    from utils.solana_client import SolanaClient
    from utils.data_processor import DataProcessor
    from utils.database import is_data_fresh
    from components.overview import render_overview
    from components.validator_metrics import render_validator_metrics
    from components.stake_distribution import render_stake_distribution
    from components.network_stats import render_network_stats
except Exception as e:
    st.error(f"🚨 Failed to import modules: {e}")
    raise
import time
import os
from utils.solana_client import SolanaClient
from utils.data_processor import DataProcessor
from utils.database import is_data_fresh
from components.overview import render_overview
from components.validator_metrics import render_validator_metrics
from components.stake_distribution import render_stake_distribution
from components.network_stats import render_network_stats

# Page configuration
st.set_page_config(
    page_title="Solana Staking Dashboard",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data caching
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = 0
if 'validators_data' not in st.session_state:
    st.session_state.validators_data = None
if 'network_data' not in st.session_state:
    st.session_state.network_data = None
if 'stake_data' not in st.session_state:
    st.session_state.stake_data = None
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 60  # Default refresh every 60 seconds

# Sidebar
st.sidebar.title("Solana Staking Dashboard")
st.sidebar.image("https://cryptologos.cc/logos/solana-sol-logo.svg", width=100)

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Validator Metrics", "Stake Distribution", "Network Statistics"]
)

# RPC endpoint selection
rpc_endpoint = st.sidebar.selectbox(
    "RPC Endpoint",
    ["https://api.mainnet-beta.solana.com", "https://solana-api.projectserum.com"]
)

# Refresh rate control
refresh_interval = st.sidebar.slider(
    "Data Refresh Interval (seconds)",
    min_value=30,
    max_value=300,
    value=st.session_state.refresh_interval,
    step=30
)
st.session_state.refresh_interval = refresh_interval

# Manual refresh button
if st.sidebar.button("Refresh Data Now"):
    st.session_state.last_update_time = 0

# Data fetch logic with caching
current_time = time.time()
should_update = (current_time - st.session_state.last_update_time) > st.session_state.refresh_interval

# Database status
from utils.database import database_available

# Show database connection status
if database_available:
    st.sidebar.success("Database caching enabled")
    
    # Check if we have fresh data in database
    if is_data_fresh(max_age_minutes=refresh_interval//60):
        st.sidebar.info("Using cached data from database")
else:
    st.sidebar.warning("Database not available. Using direct RPC calls only.")

with st.spinner("Fetching latest Solana staking data...") if should_update else st.container():
    if should_update:
        try:
            # Initialize client
            client = SolanaClient(rpc_endpoint)
            
            # Use the database-integrated methods
            # These will fetch from the database if data is fresh, or from RPC if needed
            validators_info = client.get_validators(use_cache=database_available)
            network_info = client.get_network_info(use_cache=database_available)
            stake_accounts = client.get_stake_accounts(use_cache=database_available)
            
            # Process data
            processor = DataProcessor(validators_info, network_info, stake_accounts)
            
            # Update session state
            st.session_state.validators_data = processor.get_processed_validators()
            st.session_state.network_data = processor.get_processed_network_info()
            st.session_state.stake_data = processor.get_processed_stake_info()
            st.session_state.last_update_time = current_time
            
            # Display appropriate success message
            if stake_accounts:
                st.sidebar.success(f"Data updated at {time.strftime('%H:%M:%S', time.localtime(current_time))}")
            else:
                st.sidebar.warning(f"Data partially updated at {time.strftime('%H:%M:%S', time.localtime(current_time))}. Stake account data is limited due to RPC restrictions.")
        except Exception as e:
            st.sidebar.error(f"Error fetching data: {str(e)}")
            if st.session_state.validators_data is None:  # Only show this if we have no previous data
                st.error("Failed to fetch Solana blockchain data. Please check your connection and try again.")
                st.stop()

# Display last update time
st.sidebar.info(f"Last update: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update_time))}")

# Render selected page
if page == "Overview":
    render_overview(
        st.session_state.validators_data,
        st.session_state.network_data,
        st.session_state.stake_data
    )
elif page == "Validator Metrics":
    render_validator_metrics(st.session_state.validators_data)
elif page == "Stake Distribution":
    render_stake_distribution(st.session_state.stake_data)
elif page == "Network Statistics":
    render_network_stats(st.session_state.network_data)

# Footer
st.sidebar.markdown('---')
st.sidebar.caption("Powered by Solana RPC API")
st.sidebar.caption("Data updates automatically according to the refresh interval")

# Database Information - Hidden by default, can be expanded
with st.sidebar.expander("💾 Database Information", expanded=False):
    st.markdown("### Database Caching")
    
    if database_available:
        st.success("PostgreSQL database is connected and working")
        st.info("""
        The dashboard uses a PostgreSQL database to:
        - Cache Solana blockchain data to reduce RPC calls
        - Provide historical data even when RPC limits are reached
        - Enable time series analysis of network trends
        """)
        
        # Add manual database refresh button
        if st.button("Force Database Refresh"):
            st.session_state.last_update_time = 0
            st.rerun()  # Use the newer st.rerun() instead of experimental_rerun()
    else:
        st.warning("Database is not configured or not accessible")
        st.info("""
        Without a database, the dashboard will:
        - Make all RPC calls directly to Solana
        - Be subject to RPC rate limits
        - Not be able to show historical data
        """)
