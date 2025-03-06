import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

# Function to assign clusters based on pollutant levels
def assign_clusters(row):
    pm2_5 = row['PM2.5']
    pm10 = row['PM10']
    so2 = row['SO2']
    no2 = row['NO2']
    co = row['CO']
    o3 = row['O3']

    if (0 <= pm2_5 <= 35 and 0 <= pm10 <= 50 and 0 <= so2 <= 10 and
        0 <= no2 <= 30 and 0 <= co <= 500 and 0 <= o3 <= 50):
        return 'Low Pollution'
    elif (36 <= pm2_5 <= 75 and 51 <= pm10 <= 100 and 11 <= so2 <= 20 and
          31 <= no2 <= 60 and 501 <= co <= 1000 and 51 <= o3 <= 70):
        return 'Moderate Pollution'
    else:
        return 'High Pollution'

# Apply the function to assign clusters
cleaned_dataframe['Cluster'] = cleaned_dataframe.apply(assign_clusters, axis=1)

def plot_pollution_levels_by_station(df, start_date, end_date):
    # Filter data based on selected date range
    filtered_df = df.loc[start_date:end_date]
    
    proportion_df = filtered_df.groupby(['station', 'Cluster']).size().unstack(fill_value=0)
    proportion_df = proportion_df.div(proportion_df.sum(axis=1), axis=0)
    
    fig1, ax1 = plt.subplots()
    proportion_df.plot(kind='bar', stacked=True, color=['red', 'orange', 'green'], ax=ax1)
    ax1.set_title('Proportion of Pollution Levels at Each Station')
    ax1.set_xlabel('Station')
    ax1.set_ylabel('Proportion')
    ax1.legend(title='Pollution Level')
    ax1.set_xticklabels(proportion_df.index, rotation=45)
    fig1.tight_layout()
    st.pyplot(fig1)

def plot_yearly_pollution_levels(df, start_date, end_date):
    # Filter data based on selected date range
    filtered_df = df.loc[start_date:end_date]
    
    yearly_cluster_counts = filtered_df.resample('Y').Cluster.value_counts().unstack().fillna(0)
    yearly_proportions = yearly_cluster_counts.div(yearly_cluster_counts.sum(axis=1), axis=0)
    
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    yearly_proportions.plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_title('Proporsi Tingkat Polusi per Tahun')
    ax2.set_xlabel('Tahun')
    ax2.set_ylabel('Proporsi')
    ax2.legend(title='Pollution Level')
    ax2.set_xticks(range(len(yearly_proportions.index)))
    ax2.set_xticklabels(yearly_proportions.index.strftime('%Y'), rotation=45)
    fig2.tight_layout()
    st.pyplot(fig2)

# Call the plotting functions with the filtered data
plot_temperature_data(cleaned_dataframe, start_datetime, end_datetime)
plot_temperature_heatmap(cleaned_dataframe, start_datetime, end_datetime)
plot_pollution_levels_by_station(cleaned_dataframe, start_datetime, end_datetime)
plot_yearly_pollution_levels(cleaned_dataframe, start_datetime, end_datetime)
