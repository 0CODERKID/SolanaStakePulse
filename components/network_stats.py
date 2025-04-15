import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def render_network_stats(network_data):
    """
    Render the network statistics page with detailed network information.
    
    Args:
        network_data (dict): Processed network information
    """
    st.title("Solana Network Statistics")
    
    # Check if data is available
    if network_data is None:
        st.warning("Network data is still loading. Please wait...")
        return
    
    # Epoch information
    st.subheader("Current Epoch Information")
    
    epoch_data = network_data['epoch']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Current Epoch", 
            value=f"{epoch_data['current']:,}"
        )
    
    with col2:
        st.metric(
            label="Slot Index", 
            value=f"{epoch_data['slot_index']:,}",
            delta=f"{epoch_data['progress_percentage']:.1f}% of epoch"
        )
    
    with col3:
        st.metric(
            label="Slots in Epoch", 
            value=f"{epoch_data['slots_in_epoch']:,}"
        )
    
    with col4:
        st.metric(
            label="Estimated Time Remaining", 
            value=f"{epoch_data['hours_remaining']:.1f} hours"
        )
    
    # Epoch progress visualization
    progress = epoch_data['progress_percentage'] / 100
    
    # Create a gauge chart for epoch progress
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=epoch_data['progress_percentage'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Epoch Progress", 'font': {'size': 24}},
        delta={'reference': 0, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "royalblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': 'lightblue'},
                {'range': [25, 50], 'color': 'cyan'},
                {'range': [50, 75], 'color': 'royalblue'},
                {'range': [75, 100], 'color': 'blue'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 99
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Epoch timeline
    st.subheader("Epoch Timeline")
    
    # Calculate epoch start and end times (approximation)
    now = datetime.now()
    epoch_end = now + timedelta(hours=epoch_data['hours_remaining'])
    epoch_length_hours = epoch_data['slots_in_epoch'] * 0.4 / 3600  # 0.4 seconds per slot
    epoch_start = epoch_end - timedelta(hours=epoch_length_hours)
    
    # Create a timeline visualization
    timeline_data = pd.DataFrame([
        {'Event': 'Epoch Start', 'Time': epoch_start},
        {'Event': 'Current Time', 'Time': now},
        {'Event': 'Projected End', 'Time': epoch_end}
    ])
    
    fig = px.timeline(
        timeline_data, 
        x_start='Time', 
        x_end='Time', 
        y='Event',
        color='Event',
        color_discrete_map={
            'Epoch Start': 'green',
            'Current Time': 'blue',
            'Projected End': 'red'
        }
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=200)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"""
    - **Epoch Start**: {epoch_start.strftime('%Y-%m-%d %H:%M:%S')}
    - **Current Time**: {now.strftime('%Y-%m-%d %H:%M:%S')}
    - **Projected End**: {epoch_end.strftime('%Y-%m-%d %H:%M:%S')}
    - **Total Duration**: {epoch_length_hours:.2f} hours
    """)
    
    st.markdown("---")
    
    # Inflation and staking information
    st.subheader("Inflation and Supply Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Inflation information
        st.markdown("#### Inflation Rates")
        
        inflation_data = network_data['inflation']
        
        inflation_df = pd.DataFrame({
            'Type': ['Total Inflation', 'Validator Rewards', 'Foundation'],
            'Rate (%)': [
                inflation_data['total'],
                inflation_data['validator'],
                inflation_data['foundation']
            ]
        })
        
        fig = px.bar(
            inflation_df,
            x='Type',
            y='Rate (%)',
            labels={'Rate (%)': 'Annual Rate (%)', 'Type': 'Inflation Type'},
            color='Type',
            text='Rate (%)'
        )
        
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Supply information
        st.markdown("#### SOL Supply")
        
        supply_data = network_data['supply']
        
        # Create a pie chart for supply distribution
        fig = go.Figure(data=[go.Pie(
            labels=['Staked', 'Circulating (Unstaked)'],
            values=[
                supply_data['staked'],
                supply_data['circulating'] - supply_data['staked']
            ],
            hole=.4,
            marker_colors=['royalblue', 'lightblue']
        )])
        
        fig.update_layout(
            title_text=f"SOL Supply Distribution ({supply_data['staking_ratio']:.1f}% Staked)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Supply details
    st.markdown("#### SOL Supply Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Supply", 
            value=f"{network_data['supply']['total']:,.0f} SOL"
        )
    
    with col2:
        st.metric(
            label="Circulating Supply", 
            value=f"{network_data['supply']['circulating']:,.0f} SOL",
            delta=f"{network_data['supply']['circulating']/network_data['supply']['total']*100:.1f}% of total" if network_data['supply']['total'] > 0 else None
        )
    
    with col3:
        st.metric(
            label="Total Staked", 
            value=f"{network_data['supply']['staked']:,.0f} SOL",
            delta=f"{network_data['supply']['staking_ratio']:.1f}% of circulating" if network_data['supply']['circulating'] > 0 else None
        )
    
    st.markdown("---")
    
    # Validator statistics
    st.subheader("Validator Network Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Validator status chart
        validators_data = network_data['validators']
        
        validators_df = pd.DataFrame({
            'Status': ['Active', 'Delinquent'],
            'Count': [validators_data['active'], validators_data['delinquent']]
        })
        
        fig = px.pie(
            validators_df,
            values='Count',
            names='Status',
            title=f"Validator Status Distribution (Total: {validators_data['total']})",
            color='Status',
            color_discrete_map={
                'Active': 'green',
                'Delinquent': 'red'
            }
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label+value')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Stake concentration visualization
        concentration_data = network_data['concentration']
        
        concentration_df = pd.DataFrame({
            'Validator Group': ['Top 10', 'Top 20', 'Top 50', 'Others'],
            'Stake Percentage': [
                concentration_data['top10'],
                concentration_data['top20'] - concentration_data['top10'],
                concentration_data['top50'] - concentration_data['top20'],
                100 - concentration_data['top50']
            ]
        })
        
        fig = px.bar(
            concentration_df,
            x='Validator Group',
            y='Stake Percentage',
            title='Stake Concentration by Validator Group',
            text='Stake Percentage'
        )
        
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # Stake concentration metrics
    st.markdown("#### Stake Concentration Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Top 10 Validators", 
            value=f"{network_data['concentration']['top10']:.1f}%",
            delta="of total stake"
        )
    
    with col2:
        st.metric(
            label="Top 20 Validators", 
            value=f"{network_data['concentration']['top20']:.1f}%",
            delta="of total stake"
        )
    
    with col3:
        st.metric(
            label="Top 50 Validators", 
            value=f"{network_data['concentration']['top50']:.1f}%",
            delta="of total stake"
        )
    
    # Calculate Nakamoto Coefficient
    st.markdown("#### Decentralization Metrics")
    stake_pcts = [
        network_data['concentration']['top10'] / 10,  # Approximate average for top 10
        (network_data['concentration']['top20'] - network_data['concentration']['top10']) / 10,  # Approximate for next 10
        (network_data['concentration']['top50'] - network_data['concentration']['top20']) / 30  # Approximate for next 30
    ]
    
    # Simplified calculation: how many top validators control >33% stake
    validators_for_33pct = 0
    cumulative = 0
    
    for i, pct in enumerate(stake_pcts):
        validators_in_group = 10 if i < 2 else 30
        for _ in range(validators_in_group):
            cumulative += pct
            validators_for_33pct += 1
            if cumulative > 33:
                break
        if cumulative > 33:
            break
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Nakamoto Coefficient (33%)", 
            value=f"{validators_for_33pct} validators",
            help="Estimated number of validators needed to control 33% of stake"
        )
    
    with col2:
        # Effective validator count: inverse of sum of squares of stake percentages
        # (this is a simplified approximation)
        herfindahl_index = (network_data['concentration']['top10'] / 100)**2 * 10 + \
                          ((network_data['concentration']['top20'] - network_data['concentration']['top10']) / 100)**2 * 10 + \
                          ((network_data['concentration']['top50'] - network_data['concentration']['top20']) / 100)**2 * 30 + \
                          ((100 - network_data['concentration']['top50']) / 100)**2 * 100  # Assume 100 validators in "others"
        
        effective_validators = 1 / herfindahl_index if herfindahl_index > 0 else 0
        
        st.metric(
            label="Effective Validator Count", 
            value=f"{effective_validators:.1f}",
            help="A measure of effective decentralization (higher is better)"
        )
