import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_overview(validators_data, network_data, stake_data):
    """
    Render the overview dashboard page with key metrics and visualizations.
    
    Args:
        validators_data (pandas.DataFrame): Processed validator data
        network_data (dict): Processed network information
        stake_data (dict): Processed stake account information
    """
    st.title("Solana Staking Ecosystem Overview")
    
    # Check if data is available
    if validators_data is None or network_data is None or stake_data is None:
        st.warning("Data is still loading. Please wait...")
        return
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total SOL Staked", 
            value=f"{network_data['supply']['staked']:,.0f} SOL",
            delta=f"{network_data['supply']['staking_ratio']:.2f}% of supply"
        )
    
    with col2:
        st.metric(
            label="Active Validators", 
            value=f"{network_data['validators']['active']:,}",
            delta=None
        )
    
    with col3:
        avg_apy = validators_data['estimatedAPY'].mean() if not validators_data.empty else 0
        st.metric(
            label="Average APY", 
            value=f"{avg_apy:.2f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Current Epoch", 
            value=f"{network_data['epoch']['current']:,}",
            delta=f"{network_data['epoch']['progress_percentage']:.1f}% complete"
        )
    
    st.markdown("---")
    
    # Second row - Stake distribution and validator commission
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Stake Distribution")
        
        # Create a stake concentration chart
        fig = go.Figure()
        
        # Data for the gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=network_data['concentration']['top20'],
            title={'text': "Top 20 Validators Stake %"},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "rgba(50, 100, 255, 0.8)"},
                'steps': [
                    {'range': [0, 33], 'color': "rgba(0, 200, 0, 0.4)"},
                    {'range': [33, 66], 'color': "rgba(255, 200, 0, 0.4)"},
                    {'range': [66, 100], 'color': "rgba(255, 0, 0, 0.4)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 2},
                    'thickness': 0.8,
                    'value': 66
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add text explanation
        st.markdown(f"""
        - Top 10 validators control **{network_data['concentration']['top10']:.1f}%** of stake
        - Top 20 validators control **{network_data['concentration']['top20']:.1f}%** of stake
        - Top 50 validators control **{network_data['concentration']['top50']:.1f}%** of stake
        """)
    
    with col2:
        st.subheader("Validator Commission Distribution")
        
        if not validators_data.empty:
            # Create histogram of commission rates
            commission_counts = validators_data['commission'].value_counts().reset_index()
            commission_counts.columns = ['commission', 'count']
            commission_counts = commission_counts.sort_values('commission')
            
            fig = px.bar(
                commission_counts, 
                x='commission', 
                y='count',
                labels={'commission': 'Commission %', 'count': 'Number of Validators'},
                title='Commission Rate Distribution'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            avg_commission = validators_data['commission'].mean()
            st.metric("Average Commission", f"{avg_commission:.1f}%")
        else:
            st.info("No validator data available")
    
    st.markdown("---")
    
    # Third row - Staking rewards and epoch info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Staking Rewards Info")
        
        # Create a card with inflation info
        st.markdown("""
        <style>
        .info-card {
            padding: 15px;
            border-radius: 5px;
            background-color: #f5f5f5;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="info-card">
            <b>Current Inflation Rate:</b> {network_data['inflation']['total']:.2f}%<br>
            <b>Validator Rewards:</b> {network_data['inflation']['validator']:.2f}%<br>
            <b>Foundation Rewards:</b> {network_data['inflation']['foundation']:.2f}%<br>
        </div>
        """, unsafe_allow_html=True)
        
        # APY distribution
        if not validators_data.empty:
            fig = px.histogram(
                validators_data,
                x="estimatedAPY",
                nbins=20,
                labels={'estimatedAPY': 'Estimated APY (%)'},
                title="Estimated APY Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Epoch Progress")
        
        # Create a progress bar for epoch completion
        epoch_progress = network_data['epoch']['progress_percentage']
        st.progress(epoch_progress / 100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Epoch", network_data['epoch']['current'])
            st.metric("Slots in Epoch", f"{network_data['epoch']['slots_in_epoch']:,}")
        with col2:
            st.metric("Current Slot", f"{network_data['epoch']['slot_index']:,}")
            st.metric("Time Remaining", f"{network_data['epoch']['hours_remaining']:.1f} hours")
    
    st.markdown("---")
    
    # Fourth row - Stake account size distribution
    st.subheader("Stake Account Size Distribution")
    
    distribution = stake_data['distribution']
    if distribution['categories'] and len(distribution['categories']) > 0:
        # Create a dataframe for the distribution
        df_dist = pd.DataFrame({
            'Stake Size': distribution['categories'],
            'Number of Accounts': distribution['counts'],
            'Total SOL': distribution['amounts']
        })
        
        # Create side-by-side bar charts
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_dist['Stake Size'],
            y=df_dist['Number of Accounts'],
            name='Number of Accounts',
            marker_color='rgb(55, 83, 109)'
        ))
        
        fig.add_trace(go.Bar(
            x=df_dist['Stake Size'],
            y=df_dist['Total SOL'],
            name='Total SOL',
            marker_color='rgb(26, 118, 255)',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Stake Account Distribution by Size',
            xaxis=dict(
                title='Stake Size (SOL)'
            ),
            yaxis=dict(
                title='Number of Accounts',
                side='left'
            ),
            yaxis2=dict(
                title='Total SOL',
                side='right',
                overlaying='y',
                showgrid=False
            ),
            legend=dict(
                x=0.01,
                y=0.99
            ),
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No stake distribution data available")
    
    # Footer information
    st.markdown("---")
    st.caption(f"Data updated at {network_data['updated_at']}")
