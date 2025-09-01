import plotly.express as px
import plotly.graph_objects as go

def create_price_comparison_chart(df):
    """Create a smooth animated price comparison chart"""
    fig = px.bar(
        df,
        x='product_name',
        y='price_inr',
        color='source',
        title="Price Comparison",
        labels={'price_inr': 'Price (₹)', 'product_name': 'Product'},
        animation_frame=None,  
        range_y=[0, df['price_inr'].max() * 1.1]  
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        template="plotly_dark",
        height=400,
        transition_duration=500,  
        margin=dict(t=50, b=100), 
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    
    return fig