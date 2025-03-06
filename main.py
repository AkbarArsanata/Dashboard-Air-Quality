import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # Import seaborn for heatmap
import datetime

# Set page configuration
st.set_page_config(page_title="Dashboard Kualitas Udara", layout="centered")

# URL langsung ke file CSV di Google Drive
url = "https://drive.google.com/uc?id=1naaH6_WxCXsZr_ym6XM6fwPAF7lsE_zL"

try:
    # Membaca data dari URL
    cleaned_dataframe = pd.read_csv(url)
except FileNotFoundError:
    st.error("File tidak ditemukan. Mohon periksa URL.")
    st.stop()
except pd.errors.EmptyDataError:
    st.error("File kosong. Mohon periksa file CSV.")
    st.stop()
except pd.errors.ParserError:
    st.error("Terjadi kesalahan dalam memparsing file CSV. Mohon periksa format file.")
    st.stop()
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
    st.stop()

# Convert 'tanggal' column to datetime
cleaned_dataframe['tanggal'] = pd.to_datetime(cleaned_dataframe['tanggal'])
# Set 'tanggal' as the index
cleaned_dataframe.set_index('tanggal', inplace=True)

# Urutkan indeks untuk memastikan MultiIndex terurut
cleaned_dataframe.sort_index(inplace=True)

# Title of the Dashboard
st.markdown('## Dashboard Kualitas Udara', unsafe_allow_html=True)

# Date Range Selector
start_date = cleaned_dataframe.index.min().date()
end_date = cleaned_dataframe.index.max().date()
date_range = st.date_input("Pilih Rentang Tanggal", [start_date, end_date])

# Convert date_range to proper datetime objects for DataFrame filtering
if len(date_range) == 2:
    start_date, end_date = date_range
    # Convert date objects to datetime with time at beginning and end of day
    start_datetime = pd.Timestamp(datetime.datetime.combine(start_date, datetime.time.min))
    end_datetime = pd.Timestamp(datetime.datetime.combine(end_date, datetime.time.max))
else:
    # Fallback if date range selection is incomplete
    start_datetime = pd.Timestamp(cleaned_dataframe.index.min())
    end_datetime = pd.Timestamp(cleaned_dataframe.index.max())

# Function to plot monthly averages of pollutants
def plot_monthly_pollutant_averages(df, start_date, end_date):
    # Filter data based on selected date range
    filtered_df = df.loc[start_date:end_date]
    
    monthly_avg = filtered_df.resample('M').agg({
        'PM2.5': 'mean',
        'PM10': 'mean',
        'SO2': 'mean',
        'NO2': 'mean',
        'CO': 'mean',
        'O3': 'mean'
    }).reset_index()
    monthly_avg.set_index('tanggal', inplace=True)
    
    fig4, ax4 = plt.subplots(figsize=(14, 8))
    ax4.plot(monthly_avg.index, monthly_avg[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']], marker='o')
    ax4.set_title('Rata-rata Bulanan Polutan')
    ax4.set_xlabel('Tanggal')
    ax4.set_ylabel('Konsentrasi (µg/m³)')
    ax4.legend(monthly_avg.columns[1:], title='Polutan')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig4)

# Function to calculate and plot the proportion of each pollution level at each station
def plot_pollution_proportions(df, start_date, end_date):
    # Filter data based on selected date range
    filtered_df = df.loc[start_date:end_date]
    
    # Calculate the proportion of each pollution level at each station
    proportion_df = filtered_df.groupby(['station', 'Cluster']).size().unstack(fill_value=0)
    proportion_df = proportion_df.div(proportion_df.sum(axis=1), axis=0)

    # Plotting
    fig5, ax5 = plt.subplots(figsize=(14, 8))
    proportion_df.plot(kind='bar', stacked=True, color=['red', 'orange', 'green'], ax=ax5)
    ax5.set_title('Proporsi Tingkat Polusi Berdasarkan Stasiun')
    ax5.set_xlabel('Stasiun')
    ax5.set_ylabel('Proporsi')
    ax5.legend(title='Tingkat Polusi')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig5)

# Call the plotting functions with the filtered data
plot_temperature_data(cleaned_dataframe, start_datetime, end_datetime)
plot_temperature_heatmap(cleaned_dataframe, start_datetime, end_datetime)
plot_yearly_pollution_levels(cleaned_dataframe, start_datetime, end_datetime)
plot_monthly_pollutant_averages(cleaned_dataframe, start_datetime, end_datetime)
plot_pollution_proportions(cleaned_dataframe, start_datetime, end_datetime)
