"""
Comparison Feature - Business Logic
Handles data processing and analysis text generation for the comparison tab
"""

import pandas as pd
from shared.formatters import format_number
from shared.data_loaders import sample_data, tool_sample, scenw_sample, type_sample


def prepare_type_breakdown_data(date1, date2, filter_var, filter_values, group_var):
    """
    Prepare data with WW, DP, and PP breakdowns for comparison

    Args:
        date1: First date (datetime) to compare
        date2: Second date (datetime) to compare
        filter_var: Variable to filter by ('none', 'Division', 'Type', 'Item', 'Function')
        filter_values: List of values to filter
        group_var: Variable to group by ('none', 'Division', 'Type', 'Item', 'Function')

    Returns:
        tuple: (df_date1, df_date2, group_cols) or (None, None, None) if error
            - df_date1: DataFrame for first date
            - df_date2: DataFrame for second date
            - group_cols: List of grouping columns (empty if no grouping)
    """
    try:
        # Get type_sample data for both dates
        type_date1 = type_sample[type_sample['date'] == date1].copy()
        type_date2 = type_sample[type_sample['date'] == date2].copy()

        # Apply filters if specified
        if filter_var != "none" and filter_values:
            if filter_var in type_date1.columns:
                type_date1 = type_date1[type_date1[filter_var].isin(filter_values)]
                type_date2 = type_date2[type_date2[filter_var].isin(filter_values)]

        # Determine grouping columns
        group_cols = []
        if group_var != "none" and group_var in ['Division', 'Function', 'Type', 'Item']:
            group_cols = [group_var]

        # Process each date
        def process_date(type_df, group_cols):
            if group_cols:
                # Aggregate by group
                combined = type_df.groupby(group_cols).agg({
                    'WW_Amount': 'sum',
                    'DP_Amount': 'sum',
                    'PP_Amount': 'sum',
                    'WW_Income': 'sum',
                    'DP_Income': 'sum',
                    'PP_Income': 'sum'
                }).reset_index()
            else:
                # Total aggregation (no grouping)
                totals = {
                    'WW_Amount': type_df['WW_Amount'].sum(),
                    'DP_Amount': type_df['DP_Amount'].sum(),
                    'PP_Amount': type_df['PP_Amount'].sum(),
                    'WW_Income': type_df['WW_Income'].sum(),
                    'DP_Income': type_df['DP_Income'].sum(),
                    'PP_Income': type_df['PP_Income'].sum()
                }
                combined = pd.DataFrame([totals])

            return combined

        df1 = process_date(type_date1, group_cols)
        df2 = process_date(type_date2, group_cols)

        return df1, df2, group_cols

    except Exception as e:
        print(f"Error in prepare_type_breakdown_data: {e}")
        return None, None, None


def generate_enhanced_comparison_text_updated(amount_old, amount_new, income_old, income_new, date1, date2,
                                            filter_var, filter_values, group_var, df1, df2, selected_type, amount_col, income_col):
    """
    Generate comprehensive comparison analysis text

    Args:
        amount_old: Amount value for first date
        amount_new: Amount value for second date
        income_old: Income value for first date
        income_new: Income value for second date
        date1: First date (datetime)
        date2: Second date (datetime)
        filter_var: Variable used for filtering
        filter_values: List of filter values
        group_var: Variable used for grouping
        df1: DataFrame for first date
        df2: DataFrame for second date
        selected_type: Type of data being compared (Total, Best, Type1, Type2, Type3)
        amount_col: Column name for amount data
        income_col: Column name for income data

    Returns:
        str: Comprehensive comparison analysis text
    """
    def create_change_sentence(variable, old_val, new_val, date1, date2):
        if abs((new_val - old_val) / old_val) < 0.01 if old_val != 0 else abs(new_val) < 0.01:
            change_type = "remained essentially equal"
            relative_change = 0
        elif new_val > old_val:
            change_type = "increased"
            relative_change = ((new_val - old_val) / old_val * 100) if old_val != 0 else 100
        else:
            change_type = "decreased"
            relative_change = ((new_val - old_val) / old_val * 100) if old_val != 0 else -100

        if change_type == "remained essentially equal":
            return f"{variable} amount was {old_val:.1f} in {date1.strftime('%Y-%m')} and {change_type} at {new_val:.1f} in {date2.strftime('%Y-%m')}."
        else:
            return f"{variable} amount was {old_val:.1f} in {date1.strftime('%Y-%m')} and {change_type} to {new_val:.1f} in {date2.strftime('%Y-%m')}, which corresponds to a relative {change_type.replace('increased', 'increase').replace('decreased', 'decrease')} of {abs(relative_change):.1f}%."

    text_parts = [f"COMPARISON ANALYSIS - {selected_type}:\n", "=" * 30 + "\n\n"]
    if filter_var != "none" and filter_values:
        text_parts.append(f"Analysis filtered by {filter_var}: {', '.join(filter_values)}.\n\n")

    # --- TYPE CONTRIBUTIONS TO TOTAL (shown first) ---
    _income_raw = ['Income_1', 'Income_2', 'Income_3']
    _amount_raw = ['Amount_1', 'Amount_2', 'Amount_3']
    if (not df1.empty and not df2.empty and
            all(c in df1.columns for c in _income_raw + _amount_raw)):
        inc_tot_old = df1['Income_total'].sum() if 'Income_total' in df1.columns else df1[_income_raw].sum().sum()
        inc_tot_new = df2['Income_total'].sum() if 'Income_total' in df2.columns else df2[_income_raw].sum().sum()
        amt_tot_old = df1['Amount_total'].sum() if 'Amount_total' in df1.columns else df1[_amount_raw].sum().sum()
        amt_tot_new = df2['Amount_total'].sum() if 'Amount_total' in df2.columns else df2[_amount_raw].sum().sum()

        text_parts.append("TYPE CONTRIBUTIONS TO TOTAL:\n" + "=" * 30 + "\n\n")
        text_parts.append(f"Income Contributions (% of Total Income — {format_number(inc_tot_old)} → {format_number(inc_tot_new)}):\n")
        for col in _income_raw:
            label = col.replace('_', ' ')
            val_old = df1[col].sum()
            val_new = df2[col].sum()
            pct_old = (val_old / inc_tot_old * 100) if inc_tot_old != 0 else 0
            pct_new = (val_new / inc_tot_new * 100) if inc_tot_new != 0 else 0
            text_parts.append(f"• {label}: {format_number(val_old)} ({pct_old:.1f}%) → {format_number(val_new)} ({pct_new:.1f}%)\n")
        text_parts.append("\n")

        text_parts.append(f"Amount Contributions (% of Total Amount — {format_number(amt_tot_old)} → {format_number(amt_tot_new)}):\n")
        for col in _amount_raw:
            label = col.replace('_', ' ')
            val_old = df1[col].sum()
            val_new = df2[col].sum()
            pct_old = (val_old / amt_tot_old * 100) if amt_tot_old != 0 else 0
            pct_new = (val_new / amt_tot_new * 100) if amt_tot_new != 0 else 0
            text_parts.append(f"• {label}: {format_number(val_old)} ({pct_old:.1f}%) → {format_number(val_new)} ({pct_new:.1f}%)\n")
        text_parts.append("\n")

        text_parts.append("Return Ratio by Type (Income/Amount):\n")
        for inc_col, amt_col, lbl in [('Income_1', 'Amount_1', 'Type 1'),
                                       ('Income_2', 'Amount_2', 'Type 2'),
                                       ('Income_3', 'Amount_3', 'Type 3')]:
            i_old = df1[inc_col].sum()
            i_new = df2[inc_col].sum()
            a_old = df1[amt_col].sum()
            a_new = df2[amt_col].sum()
            r_old = (i_old / a_old) if a_old != 0 else 0
            r_new = (i_new / a_new) if a_new != 0 else 0
            chg = r_new - r_old
            direction = "improved" if chg > 0 else "declined" if chg < 0 else "stable"
            text_parts.append(f"• {lbl}: {r_old:.4f} → {r_new:.4f} ({direction}, {chg:+.4f})\n")
        text_parts.append("\n")
    # -------------------------------------------------

    text_parts.append(create_change_sentence(f"Amount ({selected_type})", amount_old, amount_new, date1, date2) + "\n\n")
    text_parts.append(create_change_sentence(f"Income ({selected_type})", income_old, income_new, date1, date2) + "\n\n")

    ratio_old = (income_old / amount_old) if amount_old != 0 else 0
    ratio_new = (income_new / amount_new) if amount_new != 0 else 0
    ratio_change = ratio_new - ratio_old

    if abs(ratio_change) < 0.01:
        text_parts.append(f"The Return Ratio (Income/Amount) remained stable at approximately {ratio_old:.2f}.\n\n")
    elif ratio_change > 0:
        text_parts.append(f"The Return Ratio (Income/Amount) improved from {ratio_old:.2f} to {ratio_new:.2f}, representing an increase of {ratio_change:.2f}.\n\n")
    else:
        text_parts.append(f"The Return Ratio (Income/Amount) declined from {ratio_old:.2f} to {ratio_new:.2f}, representing a decrease of {abs(ratio_change):.2f}.\n\n")

    # Income Type Contribution Breakdown (Income_1, Income_2, Income_3)
    income_type_cols = ['Income_1', 'Income_2', 'Income_3']
    if all(col in df1.columns for col in income_type_cols) and not df1.empty and not df2.empty:
        text_parts.append("INCOME TYPE CONTRIBUTION BREAKDOWN:\n" + "=" * 30 + "\n\n")

        inc_totals_old = {col: df1[col].sum() for col in income_type_cols}
        inc_totals_new = {col: df2[col].sum() for col in income_type_cols}
        inc_total_old = sum(inc_totals_old.values())
        inc_total_new = sum(inc_totals_new.values())

        for col in income_type_cols:
            label = col.replace('_', ' ')
            val_old = inc_totals_old[col]
            val_new = inc_totals_new[col]
            pct_old = (val_old / inc_total_old * 100) if inc_total_old != 0 else 0
            pct_new = (val_new / inc_total_new * 100) if inc_total_new != 0 else 0
            val_change = val_new - val_old
            pct_change = ((val_change / val_old) * 100) if val_old != 0 else (100 if val_new > 0 else 0)
            change_desc = "increased" if val_change > 0 else "decreased" if val_change < 0 else "unchanged"
            text_parts.append(
                f"• {label}: {format_number(val_old)} ({pct_old:.1f}% of total) → {format_number(val_new)} ({pct_new:.1f}% of total) "
                f"— {change_desc} by {abs(pct_change):.1f}%\n"
            )
        text_parts.append("\n")

        # Income Type Contribution by Segment Detail (group_var)
        analysis_group = group_var if group_var != "none" else "Function"
        if analysis_group in df1.columns and analysis_group in df2.columns:
            text_parts.append(f"INCOME TYPE CONTRIBUTION BY {analysis_group.upper()}:\n" + "=" * 30 + "\n\n")

            all_segments = sorted(set(df1[analysis_group].unique()) | set(df2[analysis_group].unique()))
            for segment in all_segments:
                seg_df1 = df1[df1[analysis_group] == segment]
                seg_df2 = df2[df2[analysis_group] == segment]
                text_parts.append(f"{segment}:\n")

                for col in income_type_cols:
                    label = col.replace('_', ' ')
                    val_old = seg_df1[col].sum() if not seg_df1.empty else 0
                    val_new = seg_df2[col].sum() if not seg_df2.empty else 0
                    seg_total_old = sum(seg_df1[c].sum() for c in income_type_cols) if not seg_df1.empty else 0
                    seg_total_new = sum(seg_df2[c].sum() for c in income_type_cols) if not seg_df2.empty else 0
                    pct_old = (val_old / seg_total_old * 100) if seg_total_old != 0 else 0
                    pct_new = (val_new / seg_total_new * 100) if seg_total_new != 0 else 0
                    val_change = val_new - val_old
                    pct_change = ((val_change / val_old) * 100) if val_old != 0 else (100 if val_new > 0 else 0)
                    change_desc = "increased" if val_change > 0 else "decreased" if val_change < 0 else "unchanged"
                    text_parts.append(
                        f"  • {label}: {format_number(val_old)} ({pct_old:.1f}%) → {format_number(val_new)} ({pct_new:.1f}%) "
                        f"— {change_desc} by {abs(pct_change):.1f}%\n"
                    )
                text_parts.append("\n")

    # Determine which grouping variable to analyze (default to Item if none selected)
    analysis_group_var = group_var if group_var != "none" else "Function"

    if analysis_group_var in ['Division', 'Type', 'Item', 'Function'] and not df1.empty and not df2.empty:
        text_parts.append(f"PROPORTION ANALYSIS BY {analysis_group_var.upper()}:\n" + "=" * 30 + "\n\n")

        for col, label in [(amount_col, "Amount"), (income_col, "Income")]:
            groups1 = df1.groupby(analysis_group_var)[col].sum()
            total1 = df1[col].sum()
            props1 = (groups1 / total1 * 100) if total1 > 0 else pd.Series(dtype=float)

            groups2 = df2.groupby(analysis_group_var)[col].sum()
            total2 = df2[col].sum()
            props2 = (groups2 / total2 * 100) if total2 > 0 else pd.Series(dtype=float)

            text_parts.append(f"{label} ({selected_type}) Proportion Changes by {analysis_group_var}:\n")
            for group in sorted(set(props1.index) | set(props2.index)):
                prop1, prop2 = props1.get(group, 0), props2.get(group, 0)
                amt1, amt2 = groups1.get(group, 0), groups2.get(group, 0)
                prop_change = prop2 - prop1
                change_desc = "increased" if prop_change > 0 else "decreased" if prop_change < 0 else "remained stable"
                text_parts.append(f"• {group}: {prop1:.1f}% → {prop2:.1f}% ({change_desc} by {abs(prop_change):.1f}pp), amounts: {format_number(amt1)} → {format_number(amt2)}\n")
            text_parts.append("\n")

    # Always analyze Division contribution (stacked bar chart)
    if 'Division' in df1.columns and 'Division' in df2.columns and not df1.empty and not df2.empty:
        text_parts.append("DIVISION PERCENTAGE CONTRIBUTION:\n" + "=" * 30 + "\n\n")

        for col, label in [(amount_col, "Amount"), (income_col, "Income")]:
            div1 = df1.groupby('Division')[col].sum()
            total1 = div1.sum()
            pct1 = (div1 / total1 * 100) if total1 > 0 else pd.Series(dtype=float)

            div2 = df2.groupby('Division')[col].sum()
            total2 = div2.sum()
            pct2 = (div2 / total2 * 100) if total2 > 0 else pd.Series(dtype=float)

            text_parts.append(f"{label} ({selected_type}) Division Contribution:\n")
            for division in sorted(set(pct1.index) | set(pct2.index)):
                p1, p2 = pct1.get(division, 0), pct2.get(division, 0)
                pct_change = p2 - p1
                change_desc = "increased" if pct_change > 0 else "decreased" if pct_change < 0 else "remained stable"
                text_parts.append(f"• {division}: {p1:.1f}% → {p2:.1f}% ({change_desc} by {abs(pct_change):.1f}pp)\n")
            text_parts.append("\n")

    # Add Tool Sample (Income Correction) Analysis
    try:
        # Filter tool_sample data for the same date range and criteria
        tool_date1 = tool_sample[tool_sample['date'] == date1].copy()
        tool_date2 = tool_sample[tool_sample['date'] == date2].copy()

        # Apply same filtering criteria
        if filter_var != "none" and filter_values and filter_var in tool_date1.columns:
            tool_date1 = tool_date1[tool_date1[filter_var].isin(filter_values)]
            tool_date2 = tool_date2[tool_date2[filter_var].isin(filter_values)]

        if not tool_date1.empty or not tool_date2.empty:
            text_parts.append("INCOME CORRECTION ANALYSIS (Tool Data):\n" + "=" * 30 + "\n\n")

            # Total income corrections
            corr_total1 = tool_date1['Income_corr'].sum() if not tool_date1.empty else 0
            corr_total2 = tool_date2['Income_corr'].sum() if not tool_date2.empty else 0

            if corr_total1 > 0 or corr_total2 > 0:
                corr_change = corr_total2 - corr_total1
                corr_pct_change = (corr_change / corr_total1 * 100) if corr_total1 != 0 else (100 if corr_total2 > 0 else 0)
                change_desc = "increased" if corr_change > 0 else "decreased" if corr_change < 0 else "remained stable"

                text_parts.append(f"Total Income Correction was {format_number(corr_total1)} in {date1.strftime('%Y-%m')} and {change_desc} to {format_number(corr_total2)} in {date2.strftime('%Y-%m')}")
                if abs(corr_pct_change) > 0.01:
                    text_parts.append(f", representing a {abs(corr_pct_change):.1f}% change.\n\n")
                else:
                    text_parts.append(".\n\n")

                # Breakdown by Function
                if 'Function' in tool_date1.columns or 'Function' in tool_date2.columns:
                    text_parts.append("Income Correction by Function:\n")

                    func1 = tool_date1.groupby('Function')['Income_corr'].sum() if not tool_date1.empty and 'Function' in tool_date1.columns else pd.Series(dtype=float)
                    func2 = tool_date2.groupby('Function')['Income_corr'].sum() if not tool_date2.empty and 'Function' in tool_date2.columns else pd.Series(dtype=float)

                    all_functions = sorted(set(func1.index) | set(func2.index))
                    for function in all_functions:
                        f1, f2 = func1.get(function, 0), func2.get(function, 0)
                        f_change = f2 - f1
                        f_pct_change = (f_change / f1 * 100) if f1 != 0 else (100 if f2 > 0 else 0)
                        f_change_desc = "increased" if f_change > 0 else "decreased" if f_change < 0 else "remained stable"

                        text_parts.append(f"• {function}: {format_number(f1)} → {format_number(f2)} ({f_change_desc}")
                        if abs(f_pct_change) > 0.01:
                            text_parts.append(f" by {abs(f_pct_change):.1f}%)\n")
                        else:
                            text_parts.append(")\n")
                    text_parts.append("\n")
    except Exception as e:
        # Silently skip if tool_sample data not available
        pass

    # Add Scenario Weight Analysis
    try:
        # Filter scenw_sample data for the two comparison dates
        scenw_date1 = scenw_sample[scenw_sample['date'] == date1].copy()
        scenw_date2 = scenw_sample[scenw_sample['date'] == date2].copy()

        if not scenw_date1.empty or not scenw_date2.empty:
            text_parts.append("SCENARIO WEIGHT ANALYSIS:\n" + "=" * 30 + "\n\n")

            # Get scenario names and weights for both dates
            scenarios1 = scenw_date1.set_index('ScenName')['Weight'].to_dict() if not scenw_date1.empty else {}
            scenarios2 = scenw_date2.set_index('ScenName')['Weight'].to_dict() if not scenw_date2.empty else {}

            # Get all unique scenario names
            all_scenarios = sorted(set(scenarios1.keys()) | set(scenarios2.keys()))

            if all_scenarios:
                text_parts.append(f"Scenario Weight Changes between {date1.strftime('%Y-%m')} and {date2.strftime('%Y-%m')}:\n")

                for scenario in all_scenarios:
                    weight1 = scenarios1.get(scenario, 0)
                    weight2 = scenarios2.get(scenario, 0)

                    # Determine status
                    if weight1 == 0 and weight2 > 0:
                        status = "NEW scenario"
                        text_parts.append(f"• {scenario}: {status} with weight {weight2:.2%}\n")
                    elif weight1 == weight2:
                        status = "unchanged"
                        text_parts.append(f"• {scenario}: {weight1:.2%} → {weight2:.2%} ({status})\n")
                    elif weight2 > weight1:
                        status = "increased"
                        change = weight2 - weight1
                        text_parts.append(f"• {scenario}: {weight1:.2%} → {weight2:.2%} ({status} by {change:.2%})\n")
                    else:  # weight2 < weight1
                        status = "decreased"
                        change = weight1 - weight2
                        text_parts.append(f"• {scenario}: {weight1:.2%} → {weight2:.2%} ({status} by {change:.2%})\n")

                text_parts.append("\n")
    except Exception as e:
        # Silently skip if scenw_sample data not available
        pass

    # Add Type2 Breakdown Analysis (WW, DP, PP)
    try:
        type_df1, type_df2, type_group_cols = prepare_type_breakdown_data(date1, date2, filter_var, filter_values, group_var)

        if type_df1 is not None and type_df2 is not None:
            text_parts.append("TYPE 2 BREAKDOWN ANALYSIS (WW / DP / PP):\n" + "=" * 30 + "\n\n")

            # Amount breakdown
            if type_group_cols:
                text_parts.append(f"Amount Breakdown by {group_var}:\n")
                for idx, row1 in type_df1.iterrows():
                    group_val = row1[group_var]
                    row2 = type_df2[type_df2[group_var] == group_val]

                    if not row2.empty:
                        row2 = row2.iloc[0]
                        text_parts.append(f"\n{group_val}:\n")
                        for component in ['WW_Amount', 'DP_Amount', 'PP_Amount']:
                            val1, val2 = row1[component], row2[component]
                            change = val2 - val1
                            pct_change = (change / val1 * 100) if val1 != 0 else 0
                            change_desc = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
                            text_parts.append(f"  • {component}: {format_number(val1)} → {format_number(val2)} ({change_desc}")
                            if abs(pct_change) > 0.01:
                                text_parts.append(f" by {abs(pct_change):.1f}%)\n")
                            else:
                                text_parts.append(")\n")
            else:
                text_parts.append("Amount Breakdown Total:\n")
                row1, row2 = type_df1.iloc[0], type_df2.iloc[0]
                for component in ['WW_Amount', 'DP_Amount', 'PP_Amount']:
                    val1, val2 = row1[component], row2[component]
                    total1 = row1['WW_Amount'] + row1['DP_Amount'] + row1['PP_Amount']
                    total2 = row2['WW_Amount'] + row2['DP_Amount'] + row2['PP_Amount']
                    pct1 = (val1 / total1 * 100) if total1 > 0 else 0
                    pct2 = (val2 / total2 * 100) if total2 > 0 else 0
                    change = val2 - val1
                    change_desc = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
                    text_parts.append(f"• {component}: {format_number(val1)} ({pct1:.1f}%) → {format_number(val2)} ({pct2:.1f}%) ({change_desc})\n")

            text_parts.append("\n")

            # Income breakdown
            if type_group_cols:
                text_parts.append(f"Income Breakdown by {group_var}:\n")
                for idx, row1 in type_df1.iterrows():
                    group_val = row1[group_var]
                    row2 = type_df2[type_df2[group_var] == group_val]

                    if not row2.empty:
                        row2 = row2.iloc[0]
                        text_parts.append(f"\n{group_val}:\n")
                        for component in ['WW_Income', 'DP_Income', 'PP_Income']:
                            val1, val2 = row1[component], row2[component]
                            change = val2 - val1
                            pct_change = (change / val1 * 100) if val1 != 0 else 0
                            change_desc = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
                            text_parts.append(f"  • {component}: {format_number(val1)} → {format_number(val2)} ({change_desc}")
                            if abs(pct_change) > 0.01:
                                text_parts.append(f" by {abs(pct_change):.1f}%)\n")
                            else:
                                text_parts.append(")\n")
            else:
                text_parts.append("Income Breakdown Total:\n")
                row1, row2 = type_df1.iloc[0], type_df2.iloc[0]
                for component in ['WW_Income', 'DP_Income', 'PP_Income']:
                    val1, val2 = row1[component], row2[component]
                    total1 = row1['WW_Income'] + row1['DP_Income'] + row1['PP_Income']
                    total2 = row2['WW_Income'] + row2['DP_Income'] + row2['PP_Income']
                    pct1 = (val1 / total1 * 100) if total1 > 0 else 0
                    pct2 = (val2 / total2 * 100) if total2 > 0 else 0
                    change = val2 - val1
                    change_desc = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
                    text_parts.append(f"• {component}: {format_number(val1)} ({pct1:.1f}%) → {format_number(val2)} ({pct2:.1f}%) ({change_desc})\n")

            text_parts.append("\n")
    except Exception as e:
        # Silently skip if type breakdown data not available
        pass


    return "".join(text_parts)
