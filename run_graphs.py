import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
import imageio

# Load the data
sample = None

opf_data = pd.read_csv('/Users/baslad01/data_dump/openfoodfacts/product_data/en.openfoodfacts.org.products.csv',
                       sep='\t', encoding='utf-8', on_bad_lines='skip', nrows=sample)

# Extract the 'countries_en' column and convert it to a DataFrame
opf_data_country = opf_data[['code', 'countries_en', 'created_datetime']]

# Convert 'created_datetime' to datetime and extract the year
opf_data_country['created_datetime'] = pd.to_datetime(opf_data_country['created_datetime'])
opf_data_country['year'] = opf_data_country['created_datetime'].dt.year


# Convert the country names to strings and then to lowercase
opf_data_country['countries_en'] = opf_data_country['countries_en'].astype(str).str.lower()

# Split the 'countries_en' column by comma and expand the lists into separate rows
opf_data_country['countries_en'] = opf_data_country['countries_en'].str.split(',')
opf_data_country = opf_data_country.explode('countries_en')

# Strip any leading/trailing whitespace from the country names
opf_data_country['countries_en'] = opf_data_country['countries_en'].str.strip()

# Load the world map shapefile
url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(url)
world['SUBUNIT'] = world['SUBUNIT'].str.lower()
world = world[(world.POP_EST > 0) & (world.SUBUNIT != "antarctica")]

# Directory to save maps
output_dir = 'exports'
os.makedirs(output_dir, exist_ok=True)

max_count = opf_data_country['countries_en'].value_counts().max()
image_files = []
#%%
# Group by year and generate maps
for year in range(2014, 2024):

    country_count = opf_data_country[opf_data_country['year'] <= year]

    # Get the count of the countries_en
    country_count = country_count['countries_en'].value_counts()

    # Convert the Series to a DataFrame
    country_count = country_count.reset_index()

    # Rename the columns for clarity
    country_count.columns = ['country', 'count']

    # Merge the world map with the country count
    world_year = world.merge(country_count, left_on='SUBUNIT', right_on='country', how='left')
    world_year['count'] = world_year['count'].fillna(0)

    # Plot the map
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    world_year.boundary.plot(ax=ax)
    world_year.plot(column='count', ax=ax, legend=True, legend_kwds={'label': "Number of products"}, cmap='OrRd',
                    missing_kwds={"color": "lightgrey"}, vmin=0, vmax=max_count)
    plt.title(f'Number of products per country in {year}')

    # Save the map
    image_path = os.path.join(output_dir, f'products_per_country_{year}.png')
    plt.savefig(image_path)
    plt.close(fig)
    image_files.append(image_path)

# Create a GIF
gif_path = os.path.join(output_dir, 'products_per_country_evolution.gif')
with imageio.get_writer(gif_path, mode='I', duration=0.5) as writer:
    for image_file in image_files:
        image = imageio.imread(image_file)
        writer.append_data(image)