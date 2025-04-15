import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_validator_metrics(validators_data):
    """
    Render the validator metrics page with detailed validator information.
    
    Args:
        validators_data (pandas.DataFrame): Processed validator data
    """
    st.title("Validator Metrics")
    
    # Check if data is available
    if validators_data is None or validators_data.empty:
        st.warning("Validator data is still loading or unavailable. Please wait...")
        return
    
    # Top metrics row
    total_validators = len(validators_data)
    active_validators = validators_data[validators_data['status'] == 'Active'].shape[0]
    delinquent_validators = validators_data[validators_data['status'] == 'Delinquent'].shape[0]
    total_stake = validators_data['activatedStake'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Validators", 
            value=f"{total_validators:,}"
        )
    
    with col2:
        st.metric(
            label="Active Validators", 
            value=f"{active_validators:,}",
            delta=f"{active_validators/total_validators*100:.1f}% of total" if total_validators > 0 else None
        )
    
    with col3:
        st.metric(
            label="Delinquent Validators", 
            value=f"{delinquent_validators:,}",
            delta=f"{delinquent_validators/total_validators*100:.1f}% of total" if total_validators > 0 else None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Total Stake", 
            value=f"{total_stake:,.0f} SOL"
        )
    
    st.markdown("---")
    
    # Add filters for validators
    st.subheader("Validator Explorer")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            options=["All", "Active", "Delinquent"]
        )
    
    with col2:
        commission_range = st.slider(
            "Commission Range (%)",
            min_value=0,
            max_value=100,
            value=(0, 100)
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort By",
            options=["Stake (High to Low)", "Stake (Low to High)", "Commission (Low to High)", "Commission (High to Low)"]
        )
    
    # Apply filters
    filtered_df = validators_data.copy()
    
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    filtered_df = filtered_df[
        (filtered_df['commission'] >= commission_range[0]) & 
        (filtered_df['commission'] <= commission_range[1])
    ]
    
    # Apply sorting
    if sort_by == "Stake (High to Low)":
        filtered_df = filtered_df.sort_values('activatedStake', ascending=False)
    elif sort_by == "Stake (Low to High)":
        filtered_df = filtered_df.sort_values('activatedStake', ascending=True)
    elif sort_by == "Commission (Low to High)":
        filtered_df = filtered_df.sort_values('commission', ascending=True)
    elif sort_by == "Commission (High to Low)":
        filtered_df = filtered_df.sort_values('commission', ascending=False)
    
    # Display validators count
    st.markdown(f"**Showing {len(filtered_df)} validators**")
    
    # Create display tabs for different validator views
    table_tab, interactive_tab = st.tabs(["Standard Table", "Interactive Ranking"])
    
    # Prepare data for both views
    df_display = filtered_df[['nodePubkey', 'rank', 'activatedStake', 'stakePercentage', 'commission', 'estimatedAPY', 'status', 'lastVote', 'rootSlot', 'credits']]
    df_display = df_display.rename(columns={
        'nodePubkey': 'Validator Identity',
        'rank': 'Rank',
        'activatedStake': 'Activated Stake (SOL)',
        'stakePercentage': 'Stake %',
        'commission': 'Commission %',
        'estimatedAPY': 'Est. APY %',
        'status': 'Status',
        'lastVote': 'Last Vote',
        'rootSlot': 'Root Slot',
        'credits': 'Credits'
    })
    
    # Display standard table view
    with table_tab:
        st.dataframe(
            df_display[['Validator Identity', 'Rank', 'Activated Stake (SOL)', 'Stake %', 'Commission %', 'Est. APY %', 'Status']],
            use_container_width=True,
            hide_index=True
        )
    
    # Interactive ranking visualization with tooltips and hover animations
    with interactive_tab:
        # Let user choose how many validators to display
        top_n_validators = st.slider(
            "Number of validators to display", 
            min_value=10, 
            max_value=min(100, len(filtered_df)), 
            value=min(25, len(filtered_df)),
            step=5
        )
        
        # Allow selection of what metric to display in the bars
        visualization_metric = st.selectbox(
            "Ranking metric", 
            options=["Activated Stake (SOL)", "Stake %", "Commission %", "Est. APY %", "Credits"]
        )
        
        # Get top N validators based on chosen metric (default to stake if invalid)
        if visualization_metric == "Est. APY %":
            # For APY higher is better, so sort descending
            top_validators = df_display.sort_values("Est. APY %", ascending=False).head(top_n_validators)
            y_title = "Estimated APY (%)"
        elif visualization_metric == "Commission %":
            # For commission lower is better, so sort ascending
            top_validators = df_display.sort_values("Commission %", ascending=True).head(top_n_validators)
            y_title = "Commission (%)"
        elif visualization_metric == "Credits":
            # For credits higher is better
            top_validators = df_display.sort_values("Credits", ascending=False).head(top_n_validators)
            y_title = "Credits (Current Epoch)"
        elif visualization_metric == "Stake %":
            # For stake percentage higher is better
            top_validators = df_display.sort_values("Stake %", ascending=False).head(top_n_validators)
            y_title = "Stake (%)"
        else:
            # Default to activated stake
            top_validators = df_display.sort_values("Activated Stake (SOL)", ascending=False).head(top_n_validators)
            y_title = "Activated Stake (SOL)"
        
        # Create the interactive bar chart with hover effects
        fig = px.bar(
            top_validators,
            x="Validator Identity",
            y=visualization_metric,
            color="Status",
            color_discrete_map={
                "Active": "#00CC96",
                "Delinquent": "#EF553B"
            },
            hover_data={
                "Validator Identity": True,
                "Rank": True,
                "Activated Stake (SOL)": ":,.0f",
                "Stake %": ":.2f",
                "Commission %": ":.1f",
                "Est. APY %": ":.2f",
                "Status": True,
                "Last Vote": True,
                "Credits": True
            },
            title=f"Top {top_n_validators} Validators by {visualization_metric}",
            height=600
        )
        
        # Enhance hover tooltip formatting and overall appearance
        fig.update_traces(
            marker_line_width=1,
            marker_line_color="white",
            hovertemplate="<b>%{x}</b><br><br>" +
                          "Rank: %{customdata[0]}<br>" +
                          "Status: %{customdata[6]}<br>" +
                          "Stake: %{customdata[1]:,.0f} SOL (%{customdata[2]:.2f}%)<br>" +
                          "Commission: %{customdata[3]:.1f}%<br>" +
                          "Est. APY: %{customdata[4]:.2f}%<br>" +
                          "Credits: %{customdata[8]}<br>" +
                          "Last Vote: %{customdata[7]}<br><extra></extra>"
        )
        
        # Add hover animations and interactive features
        fig.update_layout(
            xaxis_title="Validator",
            yaxis_title=y_title,
            xaxis_tickangle=-45,
            plot_bgcolor="rgba(240, 240, 240, 0.2)",
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Arial"
            ),
            # Add animations for hover effects
            hoverdistance=100,
            hovermode="closest"
        )
        
        # Add custom hover animations
        fig.update_traces(
            # Make bars wider on hover
            selector=dict(type="bar"),
            hoverlabel_bgcolor="white",
            hoverlabel_font_size=14,
            hoverlabel_font_family="Arial",
            # Animation settings for hover effects
            hovertemplate=None
        )
        
        # Display the figure
        st.plotly_chart(fig, use_container_width=True)
        
        # Display a legend explaining the colors
        with st.expander("Understanding the Visualization"):
            st.markdown("""
            ### Interactive Validator Ranking
            
            This visualization shows the top validators ranked by your selected metric.
            
            - **Hover** over any bar to see detailed information about that validator
            - **Click** on legend items to filter validators by status
            - **Double-click** on legend to reset the view
            - **Zoom** by selecting a region or using the toolbar
            
            #### Colors
            - **Green**: Active validators
            - **Red**: Delinquent validators (not participating in consensus)
            
            #### Metrics Explained
            - **Activated Stake**: Total SOL delegated to this validator
            - **Stake %**: Percentage of total network stake on this validator
            - **Commission %**: Fee percentage the validator charges on rewards
            - **Est. APY %**: Estimated annual percentage yield (higher is better)
            - **Credits**: Performance credits earned in current epoch
            """)
            
        # New section for validator comparison
        st.markdown("---")
        st.subheader("Validator Performance Comparison")
        st.write("Select validators to compare key performance metrics side by side.")
        
        # Get a list of validators for the multiselect (limit to first 100 for performance)
        validator_list = df_display['Validator Identity'].head(100).tolist()
        
        # Allow selecting multiple validators to compare
        selected_validators = st.multiselect(
            "Select validators to compare (max 5):",
            options=validator_list,
            max_selections=5
        )
        
        if selected_validators:
            # Filter the dataframe to only include selected validators
            comparison_df = df_display[df_display['Validator Identity'].isin(selected_validators)]
            
            # One-click comparison button
            if st.button("Compare Selected Validators"):
                col1, col2 = st.columns(2)
                
                # Create metrics comparison chart
                with col1:
                    # Prepare data for radar chart
                    metrics = ['Stake %', 'Commission %', 'Est. APY %', 'Credits']
                    
                    # Normalize metrics for radar chart (0-1 scale)
                    radar_data = []
                    
                    for _, row in comparison_df.iterrows():
                        validator_name = row['Validator Identity']
                        short_name = validator_name[:10] + "..." if len(validator_name) > 10 else validator_name
                        
                        # Create a normalized metrics dictionary
                        values = {}
                        # Stake % (higher is better)
                        stake_pct = float(row['Stake %'])
                        max_stake = comparison_df['Stake %'].max()
                        values['Stake'] = stake_pct / max_stake if max_stake > 0 else 0
                        
                        # Commission % (lower is better, so invert)
                        commission = float(row['Commission %'])
                        max_commission = comparison_df['Commission %'].max()
                        # Invert so lower commission gets higher score
                        values['Commission'] = 1 - (commission / max_commission) if max_commission > 0 else 1
                        
                        # APY % (higher is better)
                        apy = float(row['Est. APY %'])
                        max_apy = comparison_df['Est. APY %'].max()
                        values['APY'] = apy / max_apy if max_apy > 0 else 0
                        
                        # Credits (higher is better)
                        credits = float(row['Credits'])
                        max_credits = comparison_df['Credits'].max()
                        values['Performance'] = credits / max_credits if max_credits > 0 else 0
                        
                        # Add to radar data
                        radar_data.append({
                            'Validator': short_name,
                            **values
                        })
                    
                    # Create radar chart using Plotly
                    radar_df = pd.DataFrame(radar_data)
                    
                    # Create the radar chart
                    fig = go.Figure()
                    
                    # Add a trace for each validator
                    for i, validator in enumerate(radar_df['Validator']):
                        fig.add_trace(go.Scatterpolar(
                            r=[
                                radar_df.loc[i, 'Stake'], 
                                radar_df.loc[i, 'Commission'],
                                radar_df.loc[i, 'APY'], 
                                radar_df.loc[i, 'Performance']
                            ],
                            theta=['Stake', 'Commission', 'APY', 'Performance'],
                            fill='toself',
                            name=validator
                        ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )
                        ),
                        title="Performance Comparison",
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("""
                    **Understanding the Radar Chart:**
                    - **Larger area** indicates better overall performance
                    - **Stake**: Higher value means more stake (normalized)
                    - **Commission**: Higher value means lower commission (inverted for comparison)
                    - **APY**: Higher value means better estimated returns
                    - **Performance**: Higher value means more credits earned in current epoch
                    """)
                
                # Side-by-side metrics table
                with col2:
                    # Display key metrics in a neat comparison table
                    comparison_metrics = comparison_df[['Validator Identity', 'Rank', 'Activated Stake (SOL)', 'Stake %', 'Commission %', 'Est. APY %', 'Credits', 'Status']]
                    
                    # Display the table
                    st.dataframe(comparison_metrics, use_container_width=True, hide_index=True)
                    
                    # Add a bar chart comparing a key metric
                    metric_to_compare = st.selectbox(
                        "Compare metric:", 
                        ["Activated Stake (SOL)", "Est. APY %", "Commission %", "Credits"]
                    )
                    
                    # Create 3D bar chart instead of 2D
                    z_values = [[0] * len(comparison_metrics)] * len(comparison_metrics)
                    
                    # Create 3D bar chart
                    bar_fig = go.Figure(data=[
                        go.Bar3d(
                            x=[i for i in range(len(comparison_metrics))],
                            y=[0] * len(comparison_metrics),
                            z=comparison_metrics[metric_to_compare].tolist(),
                            text=comparison_metrics['Validator Identity'].tolist(),
                            hoverinfo='text+z',
                            hovertext=[
                                f"Validator: {row['Validator Identity']}<br>" +
                                f"{metric_to_compare}: {row[metric_to_compare]}<br>" +
                                f"Status: {row['Status']}"
                                for _, row in comparison_metrics.iterrows()
                            ],
                            colorscale=[
                                [0, "#EF553B"],  # Red for lowest value
                                [0.5, "#FFA15A"],  # Orange for middle values
                                [1, "#00CC96"]   # Green for highest value
                            ],
                            colorbar=dict(
                                title=metric_to_compare,
                                thickness=20
                            ),
                            opacity=0.8
                        )
                    ])
                    
                    # Customize layout for 3D visualization
                    bar_fig.update_layout(
                        title=f"3D Comparison of {metric_to_compare}",
                        scene=dict(
                            xaxis=dict(
                                title="Validator",
                                ticktext=comparison_metrics['Validator Identity'].tolist(),
                                tickvals=[i for i in range(len(comparison_metrics))],
                                tickangle=-45
                            ),
                            yaxis=dict(visible=False),
                            zaxis=dict(title=metric_to_compare),
                            camera=dict(
                                eye=dict(x=1.5, y=-1.5, z=1)
                            )
                        ),
                        margin=dict(l=0, r=0, b=0, t=30),
                        height=450
                    )
                    
                    st.plotly_chart(bar_fig, use_container_width=True)
    
    st.markdown("---")
    
    # Visualizations of validator metrics
    st.subheader("Validator Performance Analysis")
    
    # Choose chart type
    chart_type = st.radio(
        "Select Chart Type",
        ["Performance Distribution", "Stake vs Commission", "Top Validators by Stake", "Stake Concentration"],
        horizontal=True
    )
    
    if chart_type == "Performance Distribution":
        # Credits distribution (performance metrics)
        if 'credits' in filtered_df.columns:
            fig = px.histogram(
                filtered_df,
                x="credits",
                color="status",
                marginal="box",
                labels={'credits': 'Credits (Current Epoch)', 'status': 'Status'},
                title="Validator Performance Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Add summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Credits", f"{filtered_df['credits'].mean():.0f}")
            with col2:
                st.metric("Median Credits", f"{filtered_df['credits'].median():.0f}")
            with col3:
                st.metric("Max Credits", f"{filtered_df['credits'].max():.0f}")
        else:
            st.info("Performance data (credits) not available")
    
    elif chart_type == "Stake vs Commission":
        # Create tabs for 2D and 3D views
        view_tab1, view_tab2 = st.tabs(["2D View", "3D View"])
        
        with view_tab1:
            # Standard 2D scatter plot
            fig = px.scatter(
                filtered_df,
                x="commission",
                y="activatedStake",
                color="status",
                size="stakePercentage",
                hover_name="nodePubkey",
                log_y=True,
                labels={
                    'commission': 'Commission (%)',
                    'activatedStake': 'Activated Stake (SOL)',
                    'status': 'Status',
                    'stakePercentage': 'Stake Percentage'
                },
                title="Validator Stake vs Commission (2D)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with view_tab2:
            # Enhanced 3D scatter plot
            # We'll use credits/performance as the z-axis for extra dimension
            if 'credits' in filtered_df.columns:
                # Prepare the data
                df_3d = filtered_df.copy()
                
                # Create the 3D scatter plot
                fig = go.Figure(data=[
                    go.Scatter3d(
                        x=df_3d[df_3d['status'] == 'Active']['commission'],
                        y=df_3d[df_3d['status'] == 'Active']['activatedStake'],
                        z=df_3d[df_3d['status'] == 'Active']['credits'],
                        mode='markers',
                        marker=dict(
                            size=df_3d[df_3d['status'] == 'Active']['stakePercentage'] * 50,  # Scaled for visibility
                            color='green',
                            opacity=0.8,
                            line=dict(width=0.5, color='white')
                        ),
                        name='Active Validators',
                        text=df_3d[df_3d['status'] == 'Active']['nodePubkey'],
                        hovertemplate=
                        "<b>%{text}</b><br>" +
                        "Commission: %{x}%<br>" +
                        "Stake: %{y:,.0f} SOL<br>" +
                        "Credits: %{z}<br>" +
                        "<extra></extra>"
                    ),
                    go.Scatter3d(
                        x=df_3d[df_3d['status'] == 'Delinquent']['commission'],
                        y=df_3d[df_3d['status'] == 'Delinquent']['activatedStake'],
                        z=df_3d[df_3d['status'] == 'Delinquent']['credits'],
                        mode='markers',
                        marker=dict(
                            size=df_3d[df_3d['status'] == 'Delinquent']['stakePercentage'] * 50,  # Scaled for visibility
                            color='red',
                            opacity=0.8,
                            line=dict(width=0.5, color='white')
                        ),
                        name='Delinquent Validators',
                        text=df_3d[df_3d['status'] == 'Delinquent']['nodePubkey'],
                        hovertemplate=
                        "<b>%{text}</b><br>" +
                        "Commission: %{x}%<br>" +
                        "Stake: %{y:,.0f} SOL<br>" +
                        "Credits: %{z}<br>" +
                        "<extra></extra>"
                    )
                ])
                
                # Update the layout
                fig.update_layout(
                    title="3D Validator Metrics Visualization",
                    scene=dict(
                        xaxis=dict(title="Commission (%)"),
                        yaxis=dict(title="Activated Stake (SOL)", type="log"),
                        zaxis=dict(title="Credits (Performance)"),
                        camera=dict(
                            eye=dict(x=1.5, y=-1.5, z=1.2)
                        )
                    ),
                    margin=dict(l=0, r=0, b=0, t=30),
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        bgcolor="rgba(255, 255, 255, 0.5)"
                    ),
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                **3D Visualization Explained:**
                - **X-axis**: Commission percentage charged by validators
                - **Y-axis**: Activated stake (SOL) in logarithmic scale
                - **Z-axis**: Performance credits earned in current epoch
                - **Bubble size**: Relative stake percentage of the network
                - **Color**: Green for active validators, red for delinquent ones
                
                This 3D visualization allows you to see relationships between three key metrics simultaneously.
                You can rotate, zoom, and pan by dragging in different directions.
                """)
            else:
                st.info("Credits data is required for 3D visualization but is currently unavailable.")
        
        # Add trend analysis
        st.markdown("### Commission vs Stake Analysis")
        # Correlation coefficient
        corr = filtered_df['commission'].corr(filtered_df['activatedStake'])
        st.markdown(f"Correlation between Commission and Stake: **{corr:.4f}**")
        
        # Average stake by commission band
        filtered_df['commission_band'] = pd.cut(
            filtered_df['commission'],
            bins=[0, 2, 5, 10, 100],
            labels=['0-2%', '2-5%', '5-10%', '10%+']
        )
        
        commission_analysis = filtered_df.groupby('commission_band').agg(
            avg_stake=('activatedStake', 'mean'),
            count=('nodePubkey', 'count')
        ).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                commission_analysis,
                x='commission_band',
                y='avg_stake',
                labels={
                    'commission_band': 'Commission Band',
                    'avg_stake': 'Average Stake (SOL)'
                },
                title="Average Stake by Commission Band"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                commission_analysis,
                x='commission_band',
                y='count',
                labels={
                    'commission_band': 'Commission Band',
                    'count': 'Number of Validators'
                },
                title="Validators by Commission Band"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Top Validators by Stake":
        # Bar chart of top validators by stake
        top_n = st.slider("Number of Validators to Show", min_value=5, max_value=50, value=20)
        top_validators = filtered_df.sort_values('activatedStake', ascending=False).head(top_n)
        
        fig = px.bar(
            top_validators,
            x='nodePubkey',
            y='activatedStake',
            color='commission',
            labels={
                'nodePubkey': 'Validator Identity',
                'activatedStake': 'Activated Stake (SOL)',
                'commission': 'Commission (%)'
            },
            title=f"Top {top_n} Validators by Stake",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "Stake Concentration":
        # Stake concentration visualization - enhanced with 3D
        stake_concentration = filtered_df.copy()
        stake_concentration = stake_concentration.sort_values('activatedStake', ascending=False)
        stake_concentration['cumulative_stake_percentage'] = stake_concentration['stakePercentage'].cumsum()
        stake_concentration['validator_percentage'] = np.arange(1, len(stake_concentration) + 1) / len(stake_concentration) * 100
        
        # Create tabs for 2D and 3D visualizations
        dim_tab1, dim_tab2 = st.tabs(["Standard 2D View", "Immersive 3D View"])
        
        with dim_tab1:
            # Standard 2D visualization
            fig = px.line(
                stake_concentration,
                x='validator_percentage',
                y='cumulative_stake_percentage',
                labels={
                    'validator_percentage': 'Percentage of Validators',
                    'cumulative_stake_percentage': 'Cumulative Stake Percentage'
                },
                title="Stake Concentration Analysis (2D)"
            )
            
            # Add reference lines for perfect distribution
            fig.add_trace(
                go.Scatter(
                    x=[0, 100],
                    y=[0, 100],
                    mode='lines',
                    line=dict(color='red', dash='dash'),
                    name='Perfect Equality'
                )
            )
            
            # Add markers for important percentiles
            for pct in [10, 20, 33, 50]:
                val_pct = pct
                stake_pct = stake_concentration[stake_concentration['validator_percentage'] >= val_pct].iloc[0]['cumulative_stake_percentage'] if not stake_concentration.empty else 0
                
                fig.add_trace(
                    go.Scatter(
                        x=[val_pct],
                        y=[stake_pct],
                        mode='markers+text',
                        marker=dict(size=10, color='blue'),
                        text=f"Top {pct}%: {stake_pct:.1f}%",
                        textposition="top right",
                        name=f"Top {pct}% Validators"
                    )
                )
            
            fig.update_layout(
                xaxis=dict(range=[0, 100]),
                yaxis=dict(range=[0, 100])
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with dim_tab2:
            # Create a 3D surface visualization of stake concentration
            # Prepare data for 3D surface
            x_range = np.linspace(0, 100, 50)  # Percentage of validators
            y_range = np.linspace(0, max(100, stake_concentration['cumulative_stake_percentage'].max()), 50)
            
            # Create mesh grid
            X, Y = np.meshgrid(x_range, y_range)
            
            # Create the Z values (height) based on stake concentration
            Z = np.zeros_like(X)
            
            # Interpolate values from our data
            for i, x_val in enumerate(x_range):
                nearest_idx = (np.abs(stake_concentration['validator_percentage'] - x_val)).argmin()
                nearest_pct = stake_concentration.iloc[nearest_idx]['cumulative_stake_percentage']
                
                for j, y_val in enumerate(y_range):
                    # Create a visualization where the height increases as we get closer to the actual curve
                    distance = abs(y_val - nearest_pct)
                    intensity = max(0, 1 - (distance / 50))  # Normalize to 0-1
                    Z[j, i] = intensity * 30  # Scale for visibility
            
            # Create 3D surface plot
            fig = go.Figure(data=[
                go.Surface(
                    z=Z,
                    x=X,
                    y=Y,
                    colorscale='Viridis',
                    opacity=0.8,
                    colorbar=dict(
                        title="Intensity",
                        thickness=20
                    )
                )
            ])
            
            # Add the actual inequality curve as a 3D line
            curve_x = stake_concentration['validator_percentage'].tolist()
            curve_y = stake_concentration['cumulative_stake_percentage'].tolist()
            curve_z = [30] * len(curve_x)  # Constant height for the line, above the surface
            
            fig.add_trace(
                go.Scatter3d(
                    x=curve_x,
                    y=curve_y,
                    z=curve_z,
                    mode='lines',
                    line=dict(color='red', width=5),
                    name='Inequality Curve'
                )
            )
            
            # Add perfect equality line
            fig.add_trace(
                go.Scatter3d(
                    x=[0, 100],
                    y=[0, 100],
                    z=[30, 30],  # Same height as the inequality curve
                    mode='lines',
                    line=dict(color='green', width=5, dash='dash'),
                    name='Perfect Equality'
                )
            )
            
            # Add markers for key percentiles
            marker_x = []
            marker_y = []
            marker_z = []
            marker_text = []
            
            for pct in [10, 20, 33, 50]:
                val_pct = pct
                stake_pct = stake_concentration[stake_concentration['validator_percentage'] >= val_pct].iloc[0]['cumulative_stake_percentage'] if not stake_concentration.empty else 0
                
                marker_x.append(val_pct)
                marker_y.append(stake_pct)
                marker_z.append(32)  # Slightly above the curve for visibility
                marker_text.append(f"Top {pct}%: {stake_pct:.1f}%")
            
            fig.add_trace(
                go.Scatter3d(
                    x=marker_x,
                    y=marker_y,
                    z=marker_z,
                    mode='markers+text',
                    marker=dict(size=5, color='yellow'),
                    text=marker_text,
                    name='Key Percentiles'
                )
            )
            
            # Update layout for 3D
            fig.update_layout(
                title="3D Stake Concentration Landscape",
                scene=dict(
                    xaxis=dict(title="Percentage of Validators", range=[0, 100]),
                    yaxis=dict(title="Cumulative Stake Percentage", range=[0, 100]),
                    zaxis=dict(title="Intensity", showticklabels=False),
                    camera=dict(
                        eye=dict(x=1.5, y=-1.5, z=0.8)
                    )
                ),
                margin=dict(l=0, r=0, b=0, t=30),
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            **3D Visualization Explained:**
            - The **red line** shows the actual stake distribution (inequality curve)
            - The **green dashed line** shows perfect equality (reference)
            - The **surface intensity** represents the proximity to the inequality curve
            - **Yellow markers** highlight key concentration points
            
            You can rotate, zoom, and explore this 3D landscape by dragging and using the camera controls.
            """)
        
        # Calculate and display Gini coefficient
        sorted_stake = filtered_df['activatedStake'].sort_values()
        n = len(sorted_stake)
        if n > 0:
            # Calculate Gini coefficient
            index = np.arange(1, n + 1)
            gini = 1 - (2 / (n * sorted_stake.sum())) * np.sum(sorted_stake * index)
            
            st.markdown(f"""
            ### Stake Distribution Analysis
            
            - **Gini Coefficient**: {gini:.4f} (0 = perfect equality, 1 = perfect inequality)
            - Top 10% validators control {stake_concentration[stake_concentration['validator_percentage'] >= 10].iloc[0]['cumulative_stake_percentage']:.1f}% of stake
            - Top 20% validators control {stake_concentration[stake_concentration['validator_percentage'] >= 20].iloc[0]['cumulative_stake_percentage']:.1f}% of stake
            - Top 33% validators control {stake_concentration[stake_concentration['validator_percentage'] >= 33].iloc[0]['cumulative_stake_percentage']:.1f}% of stake
            """)
