import plotly.graph_objects as go

values = [1, 1, 1, 1, 1, 1, 1, 1]
labels = ["eurocodepy", "ec1", "ec2", "ec5", "ec7", "ec8", "wind", "snow"]
parents = ["", "eurocodepy", "eurocodepy", "eurocodepy", "eurocodepy", "eurocodepy", "ec1", "ec1"]

fig = go.Figure(go.Treemap(
    labels = labels,
    values = values,
    parents = parents,
    marker_colors = ["pink", "royalblue", "lightgray", "purple", 
                     "cyan", "lightgray", "lightblue", "lightgreen"]
))

fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
fig.show()