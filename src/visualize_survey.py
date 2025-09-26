import pandas as pd
import matplotlib.pyplot as plt

def plot_likert(filename, sheet, full_range=False, as_percentage=True):
    # Load data
    df = pd.read_excel(filename, sheet_name=sheet)
    cols = [c for c in df.columns if c != "Q"]
    data = df[cols]

    # Prepare palette for 1-7 Likert
    likert_palette = [
        "#E57373", "#F9AB6B", "#FFD54F",  # 1-3 (reds/oranges/yellow)
        "#CED2D8",                        # 4 (neutral, light gray)
        "#A8E6A3", "#81C784", "#5A90C6"   # 5-7 (greens, blue)
    ]
    grouped_palette = ["#F9AB6B", "#CED2D8", "#5A90C6"]

    if full_range:
        # Calculate value counts for 1–7 per column
        likert_df = {col: data[col].value_counts().reindex(range(1,8), fill_value=0) for col in cols}
        likert_df = pd.DataFrame(likert_df).T
        if as_percentage:
            likert_df = likert_df.div(likert_df.sum(axis=1), axis=0) * 100
        to_plot = likert_df
        colorlist = likert_palette
        labels = [str(i) for i in range(1,8)]
    else:
        # Grouping function for 3 categories
        def likert_group(val):
            if val in [1,2,3]:
                return "Not Satisfied"
            elif val == 4:
                return "Neutral"
            elif val in [5,6,7]:
                return "Satisfied"
            else:
                return None

        grouped = {}
        for col in cols:
            mapped = data[col].map(likert_group)
            grouped_counts = mapped.value_counts().reindex(
                ["Not Satisfied", "Neutral", "Satisfied"], fill_value=0)
            grouped[col] = grouped_counts

        grouped_df = pd.DataFrame(grouped).T
        if as_percentage:
            grouped_df = grouped_df.div(grouped_df.sum(axis=1), axis=0) * 100
        to_plot = grouped_df
        colorlist = grouped_palette
        labels = to_plot.columns

    # Plot
    fig, ax = plt.subplots(figsize=(10, 4))
    left = [0] * len(to_plot)
    for i, label in enumerate(labels):
        # Use integer label for full range, string label for grouped
        col_label = int(label) if full_range else label
        ax.barh(to_plot.index, to_plot[col_label], left=left, color=colorlist[i], label=str(label))
        left += to_plot[col_label].values

    ax.set_xlabel("Percentage of Responses" if as_percentage else "Count of Responses per Individual Pattern")
    ax.set_ylabel("Pattern")
    ax.set_title("Likert Distribution per Pattern")
    ax.legend(title="Grade (1 Lowest, 7 Highest)", bbox_to_anchor=(1.05, 1), loc='upper left')
    if as_percentage:
        ax.set_xlim(0, 100)
    plt.tight_layout()
    plt.show()

# Example usage:
plot_likert("/Users/marcocalamo/Downloads/PallEvaluation (1).xlsx", "RISULTATI QUESTIONARIO", full_range=True, as_percentage=False)
# plot_likert("PallEvaluation.xlsx", "RISULTATI QUESTIONARIO", full_range=False, as_percentage=True)
