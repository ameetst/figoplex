import warnings
import pandas as pd
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import utils._mfapi_utils as mfapi_utils

warnings.filterwarnings('ignore')

def load_ticker_list(fund_type, directory):
    """
    Load mutual fund codes from a .txt file based on fund type.
    Args:
        fund_type (str): Fund type code (e.g., 'FX', 'FC', 'MC', 'SC').
        directory (str): Directory where the .txt files are located.
    Returns:
        list: List of mutual fund codes.
    """
    mf_codes_file = os.path.join(directory, f"{fund_type}.txt")
    with open(mf_codes_file, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def get_chronological_dates(num_years, ref_date=None):
    """
    Get a list of previous yearly dates in chronological order.
    Args:
        num_years (int): Number of years to go back.
        ref_date (date, optional): Reference date. Defaults to today.
    Returns:
        list: List of datetime.date objects.
    """
    if ref_date is None:
        ref_date = date.today()
    start_date = mfapi_utils.get_last_working_day_for_specific_date(ref_date)
    return mfapi_utils.get_x_previous_yearly_dates(start_date, num_years)

def calculate_yoy_returns(mf_code, dates_chronological):
    """
    Calculate year-on-year returns for a mutual fund.
    Args:
        mf_code (str): Mutual fund code.
        dates_chronological (list): List of yearly dates in chronological order.
    Returns:
        dict: {period: return%}
    """
    scheme_data = mfapi_utils.get_mf_data_direct(mf_code)
    if not scheme_data or 'data' not in scheme_data:
        return {}
    nav_data = pd.DataFrame(scheme_data['data'])
    nav_data['date'] = pd.to_datetime(nav_data['date'])
    nav_data['nav'] = pd.to_numeric(nav_data['nav'])
    nav_data = nav_data.sort_values('date')
    returns = {}
    for i in range(len(dates_chronological) - 1):
        start_date, end_date = dates_chronological[i + 1], dates_chronological[i]
        start_nav_row = nav_data[nav_data['date'] <= pd.to_datetime(start_date)].iloc[-1] if len(nav_data[nav_data['date'] <= pd.to_datetime(start_date)]) > 0 else None
        end_nav_row = nav_data[nav_data['date'] <= pd.to_datetime(end_date)].iloc[-1] if len(nav_data[nav_data['date'] <= pd.to_datetime(end_date)]) > 0 else None
        if start_nav_row is not None and end_nav_row is not None:
            yoy_return = ((end_nav_row['nav'] - start_nav_row['nav']) / start_nav_row['nav']) * 100
            period = f"{end_date.strftime('%Y-%m-%d')} to {start_date.strftime('%Y-%m-%d')}"
            returns[period] = yoy_return
        else:
            period = f"{end_date.strftime('%Y-%m-%d')} to {start_date.strftime('%Y-%m-%d')}"
            returns[period] = None
    return returns

def calculate_rolling_cagr(mf_code, dates_chronological):
    """
    Calculate rolling CAGR for a mutual fund.
    Args:
        mf_code (str): Mutual fund code.
        dates_chronological (list): List of yearly dates in chronological order.
    Returns:
        dict: {period: CAGR%}
    """
    scheme_data = mfapi_utils.get_mf_data_direct(mf_code)
    if not scheme_data or 'data' not in scheme_data:
        return {}
    nav_data = pd.DataFrame(scheme_data['data'])
    nav_data['date'] = pd.to_datetime(nav_data['date'])
    nav_data['nav'] = pd.to_numeric(nav_data['nav'])
    nav_data = nav_data.sort_values('date')
    cagr_dict = {}
    end_date = dates_chronological[0]
    for i in range(1, len(dates_chronological)):
        start_date = dates_chronological[i]
        start_nav_row = nav_data[nav_data['date'] <= pd.to_datetime(start_date)].iloc[-1] if len(nav_data[nav_data['date'] <= pd.to_datetime(start_date)]) > 0 else None
        end_nav_row = nav_data[nav_data['date'] <= pd.to_datetime(end_date)].iloc[-1] if len(nav_data[nav_data['date'] <= pd.to_datetime(end_date)]) > 0 else None
        period = f"{i}-Year Return"
        if start_nav_row is not None and end_nav_row is not None:
            start_nav, end_nav = start_nav_row['nav'], end_nav_row['nav']
            if start_nav > 0:
                years = (end_nav_row['date'] - start_nav_row['date']).days / 365.25
                cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100 if years > 0 else 0
                cagr_dict[period] = cagr
            else:
                cagr_dict[period] = None
        else:
            cagr_dict[period] = None
    return cagr_dict

def get_scheme_name(mf_code):
    """
    Get the scheme name for a mutual fund code.
    Args:
        mf_code (str): Mutual fund code.
    Returns:
        str: Scheme name or code if not found.
    """
    try:
        scheme_details = mfapi_utils.mf.get_scheme_details(mf_code)
        return scheme_details['scheme_name'] if isinstance(scheme_details, dict) and 'scheme_name' in scheme_details else mf_code
    except Exception:
        return mf_code 