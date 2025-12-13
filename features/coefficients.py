"""
Coefficients Module
Handles coefficient application to man-hours calculations
"""

from core.config import SEQ_NO_COLUMN, get_seq_coefficient


def apply_coefficients_to_dataframe(df):
    """
    Apply SEQ coefficients to base hours to get adjusted hours.
    Adds 'Coefficient' and 'Adjusted Hours' columns to the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with 'Base Hours' column

    Returns:
        pd.DataFrame: DataFrame with coefficient and adjusted hours columns added

    Note:
        Modifies the DataFrame in place and also returns it
    """
    # Apply coefficient based on SEQ number
    df['Coefficient'] = df[SEQ_NO_COLUMN].apply(get_seq_coefficient)

    # Calculate adjusted hours
    df['Adjusted Hours'] = df['Base Hours'] * df['Coefficient']

    return df


def get_coefficient_summary(df):
    """
    Generate a summary of coefficient application.

    Args:
        df (pd.DataFrame): DataFrame with coefficient and hours data

    Returns:
        pd.DataFrame: Summary grouped by coefficient showing count and totals
    """
    summary = df.groupby('Coefficient').agg({
        SEQ_NO_COLUMN: 'count',
        'Base Hours': 'sum',
        'Adjusted Hours': 'sum'
    }).rename(columns={SEQ_NO_COLUMN: 'Count'})

    return summary


def print_coefficient_summary(df):
    """
    Print a formatted summary of coefficient application.

    Args:
        df (pd.DataFrame): DataFrame with coefficient and hours data
    """
    summary = get_coefficient_summary(df)

    print("\nCoefficient Application Summary:")
    print(summary)
    print()


def validate_coefficients(df):
    """
    Validate that coefficients have been applied correctly.

    Args:
        df (pd.DataFrame): DataFrame with coefficient data

    Returns:
        tuple: (is_valid, error_message)
    """
    required_columns = ['Coefficient', 'Base Hours', 'Adjusted Hours']
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        return False, f"Missing required columns: {missing}"

    # Check that adjusted hours = base hours * coefficient
    tolerance = 0.01  # Allow small floating point differences
    df['Expected'] = df['Base Hours'] * df['Coefficient']
    df['Diff'] = abs(df['Adjusted Hours'] - df['Expected'])

    max_diff = df['Diff'].max()
    if max_diff > tolerance:
        problematic_rows = df[df['Diff'] > tolerance]
        return False, f"Coefficient calculation mismatch in {len(problematic_rows)} rows"

    df.drop(columns=['Expected', 'Diff'], inplace=True)

    return True, ""


def get_coefficient_distribution(df):
    """
    Get the distribution of different coefficients used.

    Args:
        df (pd.DataFrame): DataFrame with coefficient data

    Returns:
        dict: Dictionary of {coefficient: count}
    """
    return df['Coefficient'].value_counts().to_dict()