import pandas as pd
import matplotlib.pyplot as plt

# Load data
rq2_file = "./results/PallEvaluation.xlsx"
df_rq2 = pd.read_excel(rq2_file, sheet_name="RQ2")

# Identify question columns (ignore index/unnamed)
question_cols = [col for col in df_rq2.columns if not col.startswith('Unnamed')]

# Clean up responses into three groups
def three_group(val):
    if isinstance(val, str):
        v = val.strip().lower()
        if v == "yes":
            return "Yes"
        elif v == "no":
            return "No"
        else:
            return "Yes, but it needs more work"
    return val

# Use vibrant, colorblind-friendly palette
custom_color_map = {
    "Yes": "#4CAF50",                  # Bright green
    "No": "#F44336",                   # Vivid red
    "Yes, but it needs more work": "#FFB74D"  # Warm orange
}

# Layout configuration
n_cols = 2
n_rows = (len(question_cols) + 1) // n_cols

plt.close("all")
fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 2.5 * n_rows))
fig.patch.set_facecolor('white')

# Plot each pie
for ax, col in zip(axes.flatten(), question_cols):
    data = df_rq2[col].dropna().apply(three_group)
    counts = data.value_counts()
    
    pie_colors = [custom_color_map.get(label, "#BDBDBD") for label in counts.index]
    
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=counts.index,
        autopct="%1.1f%%",
        colors=pie_colors,
        startangle=90,
        textprops={'fontsize': 12, 'color': 'black', 'weight': 'bold'},
        wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
        pctdistance=0.75
    )
    
    ax.set_title(col.strip(), fontsize=14, fontweight='bold', pad=15)
    ax.axis('equal')

# Remove empty subplots
for i in range(len(question_cols), n_cols * n_rows):
    fig.delaxes(axes.flatten()[i])

# Adjust spacing for clarity
plt.subplots_adjust(hspace=0.6, wspace=0.4, top=0.95, bottom=0.05)
#plt.suptitle("Responses by Question", fontsize=18, fontweight='bold', y=0.99)

plt.show()
