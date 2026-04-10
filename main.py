import io
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV Data Analyzer", layout="wide")


@st.cache_data

def load_file(uploaded_file) -> pd.DataFrame:
    """Load CSV or Excel file into a DataFrame."""
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file type. Please upload CSV or Excel.")



def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()



def get_categorical_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()



def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    filtered_df = df.copy()

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            min_val = float(df[col].min())
            max_val = float(df[col].max())
            if min_val != max_val:
                selected_range = st.sidebar.slider(
                    f"{col}",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                )
                filtered_df = filtered_df[
                    filtered_df[col].between(selected_range[0], selected_range[1])
                ]
        else:
            unique_vals = df[col].dropna().astype(str).unique().tolist()
            if 1 < len(unique_vals) <= 30:
                selected_vals = st.sidebar.multiselect(
                    f"{col}",
                    options=sorted(unique_vals),
                    default=sorted(unique_vals),
                )
                filtered_df = filtered_df[
                    filtered_df[col].astype(str).isin(selected_vals)
                ]

    return filtered_df



def show_basic_overview(df: pd.DataFrame) -> None:
    st.subheader("Dataset Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{df.shape[0]:,}")
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing Values", int(df.isna().sum().sum()))
    c4.metric("Duplicate Rows", int(df.duplicated().sum()))



def show_data_preview(df: pd.DataFrame) -> None:
    st.subheader("Data Preview")
    st.dataframe(df, use_container_width=True)



def show_summary_stats(df: pd.DataFrame) -> None:
    st.subheader("Summary Statistics")
    numeric_cols = get_numeric_columns(df)
    if numeric_cols:
        st.dataframe(df[numeric_cols].describe().T, use_container_width=True)
    else:
        st.info("No numeric columns found for summary statistics.")



def bar_chart(df: pd.DataFrame, category_col: str, value_col: Optional[str]) -> None:
    plot_df = df.copy()
    fig, ax = plt.subplots(figsize=(10, 5))

    if value_col:
        grouped = plot_df.groupby(category_col, dropna=False)[value_col].sum().sort_values(ascending=False).head(15)
        grouped.plot(kind="bar", ax=ax)
        ax.set_ylabel(f"Sum of {value_col}")
    else:
        counts = plot_df[category_col].astype(str).value_counts().head(15)
        counts.plot(kind="bar", ax=ax)
        ax.set_ylabel("Count")

    ax.set_title("Bar Chart")
    ax.set_xlabel(category_col)
    st.pyplot(fig)



def line_chart(df: pd.DataFrame, x_col: str, y_col: str) -> None:
    plot_df = df.copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    plot_df = plot_df.sort_values(by=x_col)
    ax.plot(plot_df[x_col], plot_df[y_col])
    ax.set_title("Line Chart")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    plt.xticks(rotation=45)
    st.pyplot(fig)



def pie_chart(df: pd.DataFrame, category_col: str) -> None:
    counts = df[category_col].astype(str).value_counts().head(10)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%")
    ax.set_title("Pie Chart")
    st.pyplot(fig)



def show_charts(df: pd.DataFrame) -> None:
    st.subheader("Charts")

    numeric_cols = get_numeric_columns(df)
    categorical_cols = get_categorical_columns(df)
    all_cols = df.columns.tolist()

    chart_type = st.selectbox("Select chart type", ["Bar", "Line", "Pie"])

    if chart_type == "Bar":
        col1, col2 = st.columns(2)
        with col1:
            category_col = st.selectbox("Category column", all_cols, key="bar_cat")
        with col2:
            value_options = [None] + numeric_cols
            value_col = st.selectbox("Value column (optional)", value_options, key="bar_val")
        bar_chart(df, category_col, value_col)

    elif chart_type == "Line":
        if len(numeric_cols) == 0:
            st.info("Need at least one numeric column for a line chart.")
            return
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("X-axis column", all_cols, key="line_x")
        with col2:
            y_col = st.selectbox("Y-axis column", numeric_cols, key="line_y")
        line_chart(df, x_col, y_col)

    elif chart_type == "Pie":
        if len(categorical_cols) == 0:
            st.info("Need at least one categorical column for a pie chart.")
            return
        category_col = st.selectbox("Category column", categorical_cols, key="pie_cat")
        pie_chart(df, category_col)



def make_download(df: pd.DataFrame) -> None:
    st.subheader("Download Filtered Data")
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name="filtered_data.csv",
        mime="text/csv",
    )



def main() -> None:
    st.title("*Jiten* Data Analyzer Dashboard")
    st.write("Upload a CSV or Excel file to explore, filter, analyze, and download the data.")

    uploaded_file = st.file_uploader(
        "Upload file",
        type=["csv", "xlsx", "xls"],
    )

    if uploaded_file is None:
        st.info("Upload a CSV or Excel file to get started.")
        return

    try:
        df = load_file(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read file: {exc}")
        return

    show_basic_overview(df)
    filtered_df = apply_filters(df)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Preview",
        "Summary",
        "Charts",
        "Download",
    ])

    with tab1:
        show_data_preview(filtered_df)

    with tab2:
        show_summary_stats(filtered_df)

    with tab3:
        show_charts(filtered_df)

    with tab4:
        make_download(filtered_df)


if __name__ == "__main__":
    main()
