import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Data Visualization App", layout="wide")

st.title("Interactive Data Visualization")

# Sidebar
st.sidebar.header("Configuration")

# File upload
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=['csv'])

if uploaded_file is not None:
    # Load dataframe
    df = pd.read_csv(uploaded_file)
    
    st.sidebar.success(f"File loaded: {uploaded_file.name}")
    st.sidebar.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Plot type selection
    plot_type = st.sidebar.selectbox(
        "Select Plot Type",
        ["Scatter Plot", "Bar Plot"]
    )
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    all_cols = df.columns.tolist()
    
    # Column selection for X and Y
    x_column = st.sidebar.selectbox("Select X-axis column", all_cols)
    y_column = st.sidebar.selectbox("Select Y-axis column", numeric_cols)
    color_column = None
    if plot_type == "Scatter Plot":
        color_column = st.sidebar.selectbox("Select Color column (optional)", [None] + all_cols)
    
    # Process button
    process_button = st.sidebar.button("📈 Generate Plot", type="primary")
    
    # Main area
    if process_button:
        st.subheader(f"{plot_type}: {y_column} vs {x_column}")
        
        try:
            # Generate plot based on selection
            if plot_type == "Scatter Plot":
                fig = px.scatter(
                    df, 
                    x=x_column, 
                    y=y_column,
                    color=color_column,
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    title=f"{y_column} vs {x_column}"
                )
            else:  # Bar Plot
                fig = px.bar(
                    df, 
                    x=x_column, 
                    y=y_column,
                    title=f"{y_column} by {x_column}"
                )
                fig.update_traces(marker_color='#A23B72', opacity=0.8)

            
            # Update layout
            fig.update_layout(
                xaxis_title=x_column,
                yaxis_title=y_column,
                
                height=600
            )
            
            # Display plot
            st.plotly_chart(fig, use_container_width=True)
            
            # Show data preview
            with st.expander("📋 View Data"):
                st.dataframe(df)
                
        except Exception as e:
            st.error(f"Error generating plot: {str(e)}")
    else:
        st.info("👈 Configure your plot in the sidebar and click 'Generate Plot'")
        
        # Show data preview before plotting
        with st.expander("📋 Preview Data"):
            st.dataframe(df.head(10))
else:
    st.info("👈 Please upload a CSV file to get started")
