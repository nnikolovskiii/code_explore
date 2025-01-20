import plotly.graph_objects as go

# Data
categories = ["On context questions", "On no-context questions"]
original_values = [82, 78]
context_enhanced_values = [95, 87]

# Create the bar chart
fig = go.Figure()

# Add bars for "original"
fig.add_trace(go.Bar(
    x=categories,
    y=original_values,
    name="Original",
    marker_color='blue'  # Color for original
))

# Add bars for "context-enhanced"
fig.add_trace(go.Bar(
    x=categories,
    y=context_enhanced_values,
    name="Context-Enhanced",
    marker_color='orange'  # Color for context-enhanced
))

# Customize layout
fig.update_layout(
    title="Comparison of Original and Context-Enhanced Values",
    xaxis_title="Question Type",
    yaxis_title="Values",
    barmode='group',  # Group bars side by side
    template='plotly_white'
)

# Show the plot
fig.show()
