import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_stake_distribution(stake_data):
    """
    Render the stake distribution page with visualizations and analysis.
    
    Args:
        stake_data (dict): Processed stake account information
    """
    st.title("Stake Distribution Analysis")
    
    # Check if data is available
    if stake_data is None:
        st.warning("Stake data is still loading. Please wait...")
        return
    
    # Check if stake data is empty due to RPC limits
    if stake_data['total_accounts'] == 0:
        st.warning("Limited stake data available due to RPC restrictions. The Solana RPC has limits on retrieving large datasets. The dashboard is showing other available metrics, but stake distribution data is limited.")
        # Continue execution to show available metrics
    
    # Top metrics row
    col1, col2, col3 = st.columns(3)
    
    # Check if total_stake exists and is not None
    if 'total_stake' in stake_data and stake_data['total_stake'] is not None:
        with col1:
            st.metric(
                label="Total Stake", 
                value=f"{stake_data['total_stake']:,.0f} SOL"
            )
    else:
        with col1:
            st.metric(
                label="Total Stake", 
                value="No data"
            )
    
    # Check if total_accounts exists and is not None
    if 'total_accounts' in stake_data and stake_data['total_accounts'] is not None:
        with col2:
            st.metric(
                label="Total Stake Accounts", 
                value=f"{stake_data['total_accounts']:,}"
            )
    else:
        with col2:
            st.metric(
                label="Total Stake Accounts", 
                value="No data"
            )
    
    # Calculate average stake size if possible
    with col3:
        if ('total_stake' in stake_data and stake_data['total_stake'] is not None and 
            'total_accounts' in stake_data and stake_data['total_accounts'] is not None and 
            stake_data['total_accounts'] > 0):
            avg_stake_size = stake_data['total_stake'] / stake_data['total_accounts']
            st.metric(
                label="Average Stake Size", 
                value=f"{avg_stake_size:,.2f} SOL"
            )
        else:
            st.metric(
                label="Average Stake Size", 
                value="No data"
            )
    
    st.markdown("---")
    
    # Stake distribution charts
    st.subheader("Stake Account Size Distribution")
    
    # Check if distribution data exists
    if 'distribution' in stake_data and stake_data['distribution'] is not None:
        distribution = stake_data['distribution']
        # Check if there are categories to display
        if ('categories' in distribution and distribution['categories'] and 
            len(distribution['categories']) > 0):
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["Account Count", "SOL Amount", "Combined View"])
            
            # Create a dataframe for the distribution
            df_dist = pd.DataFrame({
                'Stake Size': distribution['categories'],
                'Number of Accounts': distribution['counts'],
                'Total SOL': distribution['amounts']
            })
            
            with tab1:
                # Account count by size category
                fig = px.bar(
                    df_dist,
                    x='Stake Size',
                    y='Number of Accounts',
                    labels={
                        'Stake Size': 'Stake Size (SOL)',
                        'Number of Accounts': 'Number of Accounts'
                    },
                    title='Stake Account Distribution by Count'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Add pie chart for percentage view
                fig = px.pie(
                    df_dist,
                    values='Number of Accounts',
                    names='Stake Size',
                    title='Account Count Percentage by Stake Size'
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                # SOL amount by size category
                fig = px.bar(
                    df_dist,
                    x='Stake Size',
                    y='Total SOL',
                    labels={
                        'Stake Size': 'Stake Size (SOL)',
                        'Total SOL': 'Total SOL Staked'
                    },
                    title='SOL Distribution by Stake Account Size'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Add pie chart for percentage view
                fig = px.pie(
                    df_dist,
                    values='Total SOL',
                    names='Stake Size',
                    title='SOL Distribution Percentage by Stake Size'
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
            with tab3:
                # Combined view
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
                    title='Combined Stake Account Distribution',
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
                
                # Calculate and display percentiles
                accounts = stake_data['accounts']
                if accounts:
                    balances = [account['balance'] for account in accounts]
                    df_accounts = pd.DataFrame({'balance': balances})
                    
                    percentiles = [10, 25, 50, 75, 90, 95, 99]
                    percentile_values = np.percentile(df_accounts['balance'], percentiles)
                    
                    st.subheader("Stake Size Percentiles")
                    
                    percentile_df = pd.DataFrame({
                        'Percentile': [f"{p}th" for p in percentiles],
                        'SOL Value': percentile_values
                    })
                    
                    st.dataframe(percentile_df, use_container_width=True, hide_index=True)
    else:
        st.info("No stake distribution data available")
    
    st.markdown("---")
    
    # Stake account samples
    st.subheader("Sample Stake Accounts")
    
    # Check if accounts key exists and has data
    if 'accounts' in stake_data and stake_data['accounts']:
        accounts = stake_data['accounts']
        # Convert to DataFrame for display
        df_accounts = pd.DataFrame(accounts)
        
        # Simplify display
        df_display = df_accounts[['pubkey', 'balance']].copy()
        df_display.columns = ['Stake Account', 'Balance (SOL)']
        
        # Allow sorting
        st.dataframe(
            df_display.sort_values('Balance (SOL)', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption("Showing sample of stake accounts (limited to 100 for performance)")
    else:
        st.info("No stake account samples available")
    
    st.markdown("---")
    
    # Analysis section
    st.subheader("Stake Distribution Analysis")
    
    # Check if distribution data exists and has categories
    if ('distribution' in stake_data and stake_data['distribution'] is not None and
        'categories' in stake_data['distribution'] and 
        stake_data['distribution']['categories'] and 
        len(stake_data['distribution']['categories']) > 0):
        
        distribution = stake_data['distribution']
        df_dist = pd.DataFrame({
            'Stake Size': distribution['categories'],
            'Number of Accounts': distribution['counts'],
            'Total SOL': distribution['amounts']
        })
        
        # Calculate percentage of accounts and SOL in each category
        df_dist['Account %'] = df_dist['Number of Accounts'] / df_dist['Number of Accounts'].sum() * 100
        df_dist['SOL %'] = df_dist['Total SOL'] / df_dist['Total SOL'].sum() * 100
        
        # Find the category with the most accounts and most SOL
        most_accounts_category = df_dist.loc[df_dist['Number of Accounts'].idxmax()]['Stake Size']
        most_sol_category = df_dist.loc[df_dist['Total SOL'].idxmax()]['Stake Size']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Most Common Account Size", most_accounts_category)
            st.metric(
                "Accounts in this Category", 
                f"{df_dist.loc[df_dist['Stake Size'] == most_accounts_category, 'Number of Accounts'].iloc[0]:,}",
                f"{df_dist.loc[df_dist['Stake Size'] == most_accounts_category, 'Account %'].iloc[0]:.1f}% of total"
            )
        
        with col2:
            st.metric("Category with Most SOL", most_sol_category)
            st.metric(
                "SOL in this Category", 
                f"{df_dist.loc[df_dist['Stake Size'] == most_sol_category, 'Total SOL'].iloc[0]:,.0f}",
                f"{df_dist.loc[df_dist['Stake Size'] == most_sol_category, 'SOL %'].iloc[0]:.1f}% of total"
            )
        
        # Add commentary on distribution
        st.markdown("""
        ### Distribution Insights
        
        The stake distribution analysis provides insights into how SOL is distributed among stake accounts of different sizes:
        """)
        
        # Generate insights based on data
        large_stake_pct = df_dist[df_dist['Stake Size'] == '100K+']['SOL %'].iloc[0] if '100K+' in df_dist['Stake Size'].values else 0
        small_stake_pct = df_dist[df_dist['Stake Size'] == '0-100']['Account %'].iloc[0] if '0-100' in df_dist['Stake Size'].values else 0
        
        insights = []
        
        if large_stake_pct > 50:
            insights.append(f"- **High Concentration**: Large stake accounts (100K+ SOL) hold {large_stake_pct:.1f}% of all staked SOL, indicating significant concentration.")
        elif large_stake_pct > 30:
            insights.append(f"- **Moderate Concentration**: Large stake accounts (100K+ SOL) hold {large_stake_pct:.1f}% of all staked SOL.")
        
        if small_stake_pct > 50:
            insights.append(f"- **Wide Participation**: Small stake accounts (0-100 SOL) represent {small_stake_pct:.1f}% of all accounts, indicating broad participation.")
        
        middle_tiers = ['100-1K', '1K-10K', '10K-100K']
        middle_sol_pct = df_dist[df_dist['Stake Size'].isin(middle_tiers)]['SOL %'].sum()
        
        if middle_sol_pct > 40:
            insights.append(f"- **Strong Middle Tier**: Mid-sized stake accounts (100-100K SOL) represent {middle_sol_pct:.1f}% of all staked SOL, indicating a healthy middle tier.")
        
        if not insights:
            insights.append("- Distribution appears balanced across different stake account sizes.")
        
        for insight in insights:
            st.markdown(insight)
    else:
        st.info("Not enough data for distribution analysis")
