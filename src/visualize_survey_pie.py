import pandas as pd
import matplotlib.pyplot as plt

# Load data
rq2_file = "/Users/marcocalamo/Downloads/PallEvaluation (1).xlsx"
df_rq2 = pd.read_excel(rq2_file, sheet_name="RQ2")

# Identify question columns (ignore index/unnamed)
question_cols = [col for col in df_rq2.columns if col != 'Unnamed: 0']

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

custom_color_map = {
    "Yes": "#A8E6A3",
    "No": "#E57373",
    "Yes, but it needs more work": "#CED2D8"
}

n_cols = 2
n_rows = (len(question_cols) + 1) // n_cols

plt.close("all")
fig, axes = plt.subplots(n_rows, n_cols, figsize=(8, 1 * n_rows))  # Bigger pies!

for ax, col in zip(axes.flatten(), question_cols):
    data = df_rq2[col].dropna().apply(three_group)
    counts = data.value_counts()
    pie_colors = [custom_color_map.get(label, "#CED2D8") for label in counts.index]
    ax.pie(
        counts, 
        labels=counts.index, 
        autopct="%1.1f%%", 
        colors=pie_colors, 
        startangle=90, 
        textprops={'fontsize': 18},
        radius=1.2  # Make each pie larger
    )
    ax.set_title(col.strip(), fontsize=15, fontweight='bold')  # Bold and bigger

# Hide unused subplots
for i in range(len(question_cols), n_cols * n_rows):
    fig.delaxes(axes.flatten()[i])

#plt.subplots_adjust(hspace=0.8, wspace=0.7)
plt.show()