import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # Import seaborn for heatmap
import datetime
from windrose import WindroseAxes
import numpy as np

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

def plot_temperature_data(df, start_date, end_date):
    # Check if 'TEMP' column exists
    if 'TEMP' not in df.columns:
        st.error("Kolom 'TEMP' tidak ditemukan dalam DataFrame.")
        return
    
    # Ensure start_date and end_date are within the DataFrame index
    if start_date < df.index.min() or end_date > df.index.max():
        st.error("Rentang tanggal yang dipilih berada di luar data yang tersedia.")
        return
    
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[start_date:end_date]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    stations = filtered_df['station'].unique()
    
    # Resample for monthly frequency and calculate mean temperature
    monthly_data = filtered_df.resample('M')['TEMP'].mean().reset_index()
    
    # Create plot
    plt.figure(figsize=(14, 8))
    
    for station in stations:
        station_data = filtered_df[filtered_df['station'] == station]
        monthly_station_data = station_data.resample('M')['TEMP'].mean()
        plt.plot(monthly_station_data.index, monthly_station_data, label=station, marker='o')
    
    plt.title('Rata-rata Suhu Tahunan per Stasiun')
    plt.xlabel('Tanggal')
    plt.ylabel('Suhu (°C)')
    plt.legend(title='Stasiun')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(plt)

# Function to plot temperature heatmap
def plot_temperature_heatmap(df, start_date, end_date):
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[start_date:end_date]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    # Extract hour and date from index
    filtered_df['hour'] = filtered_df.index.hour
    filtered_df['date'] = filtered_df.index.date
    
    # Group by date and hour, then calculate mean temperature
    heatmap_data = filtered_df.groupby(['date', 'hour'])['TEMP'].mean().unstack()
    
    # Create heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, cmap='coolwarm', annot=False, cbar_kws={'label': 'Suhu (°C)'})
    
    plt.title('Heatmap Suhu Rata-rata Berdasarkan Jam')
    plt.xlabel('Jam dalam Sehari')
    plt.ylabel('Tanggal')
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    st.pyplot(plt)

# Mengubah arah angin dari teks menjadi derajat
def wind_direction_to_degrees(direction):
    directions = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    return directions.get(direction, np.nan)

# Function to plot wind rose
def plot_wind_rose(df, start_date, end_date):
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[start_date:end_date]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    # Mengaplikasikan fungsi ke kolom 'wd'
    filtered_df['wd_deg'] = filtered_df['wd'].apply(wind_direction_to_degrees)
    
    # Menghapus baris dengan nilai NaN di kolom 'wd_deg'
    filtered_df = filtered_df.dropna(subset=['wd_deg', 'WSPM'])
    
    # Membuat plot wind rose
    fig = plt.figure(figsize=(10, 8))
    ax = WindroseAxes.from_ax(fig=fig)
    ax.bar(filtered_df['wd_deg'], filtered_df['WSPM'], normed=True, opening=0.8, edgecolor='white')
    ax.set_legend(title="Kecepatan Angin (m/s)")
    ax.set_title("Rata - rata kecepatan angin")
    
    # Menampilkan plot
    st.pyplot(fig)

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

# Function to plot yearly proportions of pollution levels
def plot_yearly_pollution_levels(df, start_date, end_date):
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[start_date:end_date]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    yearly_cluster_counts = filtered_df.resample('Y').Cluster.value_counts().unstack().fillna(0)
    yearly_proportions = yearly_cluster_counts.div(yearly_cluster_counts.sum(axis=1), axis=0)
    
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    yearly_proportions.plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_title('Proporsi Tingkat Polusi per Tahun')
    ax2.set_xlabel('Tahun')
    ax2.set_ylabel('Proporsi')
    ax2.legend(title='Tingkat Polusi')
    ax2.set_xticks(range(len(yearly_proportions.index)))
    ax2.set_xticklabels(yearly_proportions.index.strftime('%Y'), rotation=45)
    fig2.tight_layout()
    st.pyplot(fig2)

# Function to plot monthly averages of pollutants
def plot_monthly_pollutant_averages(df, start_date, end_date):
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[start_date:end_date]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    monthly_avg = filtered_df.resample('M').agg({
        'PM2.5': 'mean',
        'PM10': 'mean',
        'SO2': 'mean',
        'NO2': 'mean',
        'CO': 'mean',
        'O3': 'mean'
    }).reset_index()
    
    # Set 'tanggal' as the index for plotting
    monthly_avg.set_index('tanggal', inplace=True)
    
    fig4, ax4 = plt.subplots(figsize=(14, 8))
    ax4.plot(monthly_avg.index, monthly_avg['PM2.5'], label='PM2.5', marker='o')
    ax4.plot(monthly_avg.index, monthly_avg['PM10'], label='PM10', marker='o')
    ax4.plot(monthly_avg.index, monthly_avg['SO2'], label='SO2', marker='o')
    ax4.plot(monthly_avg.index, monthly_avg['NO2'], label='NO2', marker='o')
    ax4.plot(monthly_avg.index, monthly_avg['CO'], label='CO', marker='o')
    ax4.plot(monthly_avg.index, monthly_avg['O3'], label='O3', marker='o')
    
    ax4.set_title('Rata-rata Bulanan Polutan')
    ax4.set_xlabel('Tanggal')
    ax4.set_ylabel('Konsentrasi (µg/m³)')
    ax4.legend(title='Polutan')
    ax4.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig4)

# Function to plot average pollutants against wind direction
def plot_average_pollutants_vs_wind_direction(df, start_date, end_date):
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[start_date:end_date]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    # Mengambil kolom yang diperlukan
    df = filtered_df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'wd']].copy()

    # Menghitung rata-rata untuk setiap polutan berdasarkan arah angin
    average_pollutants = df.groupby('wd').mean().reset_index()

    # Set up the matplotlib figure
    plt.figure(figsize=(14, 8))

    # Create a scatter plot for each pollutant against wind direction
    sns.scatterplot(data=average_pollutants, x='wd', y='PM2.5', label='PM2.5', marker='o')
    sns.scatterplot(data=average_pollutants, x='wd', y='PM10', label='PM10', marker='s')
    sns.scatterplot(data=average_pollutants, x='wd', y='SO2', label='SO2', marker='^')
    sns.scatterplot(data=average_pollutants, x='wd', y='NO2', label='NO2', marker='x')
    sns.scatterplot(data=average_pollutants, x='wd', y='CO', label='CO', marker='D')
    sns.scatterplot(data=average_pollutants, x='wd', y='O3', label='O3', marker='*')

    # Adding titles and labels
    plt.title('Rata-rata Konsentrasi Polutan Berdasarkan Arah Angin')
    plt.xlabel('Arah Angin')
    plt.ylabel('Konsentrasi (µg/m³)')
    plt.xticks(rotation=45)
    plt.legend(title='Polutan')
    plt.grid(True)
    plt.tight_layout()

    # Menampilkan plot
    st.pyplot(plt)


import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_average_pollutants_vs_wind_direction(df):
    # Memastikan DataFrame memiliki kolom yang diperlukan
    required_columns = ['wd', 'WSPM', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"DataFrame harus memiliki kolom '{col}'.")

    # Mengubah arah angin dari teks menjadi derajat
    def wind_direction_to_degrees(direction):
        directions = {
            'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
            'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
            'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
            'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
        }
        return directions.get(direction, np.nan)

    # Mengaplikasikan fungsi ke kolom 'wd'
    df['wd_deg'] = df['wd'].apply(wind_direction_to_degrees)

    # Menghapus baris dengan nilai NaN di kolom 'wd_deg'
    df = df.dropna(subset=['wd_deg'])

    # Menghitung rata-rata untuk setiap polutan berdasarkan arah angin
    average_pollutants = df.groupby('wd_deg').mean().reset_index()

    # Set up the matplotlib figure
    plt.figure(figsize=(14, 8))

    # Create a scatter plot for each pollutant against wind direction
    sns.scatterplot(data=average_pollutants, x='wd_deg', y='PM2.5', label='PM2.5', marker='o')
    sns.scatterplot(data=average_pollutants, x='wd_deg', y='PM10', label='PM10', marker='s')
    sns.scatterplot(data=average_pollutants, x='wd_deg', y='SO2', label='SO2', marker='^')
    sns.scatterplot(data=average_pollutants, x='wd_deg', y='NO2', label='NO2', marker='x')
    sns.scatterplot(data=average_pollutants, x='wd_deg', y='CO', label='CO', marker='D')
    sns.scatterplot(data=average_pollutants, x='wd_deg', y='O3', label='O3', marker='P')

    # Adding titles and labels
    plt.title('Rata-rata Konsentrasi Polutan Berdasarkan Arah Angin')
    plt.xlabel('Arah Angin (Derajat)')
    plt.ylabel('Konsentrasi (µg/m³)')
    plt.legend(title='Polutan')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Menampilkan plot
    plt.show()

# Example usage
plot_average_pollutants_vs_wind_direction(cleaned_dataframe)

# Call the new plotting function in the main script
plot_average_pollutants_vs_wind_direction(cleaned_dataframe, start_datetime, end_datetime)
# Call the plotting functions with the filtered data
plot_temperature_data(cleaned_dataframe, start_datetime, end_datetime)
plot_temperature_heatmap(cleaned_dataframe, start_datetime, end_datetime)
plot_wind_rose(cleaned_dataframe, start_datetime, end_datetime)
plot_yearly_pollution_levels(cleaned_dataframe, start_datetime, end_datetime)
plot_monthly_pollutant_averages(cleaned_dataframe, start_datetime, end_datetime)
