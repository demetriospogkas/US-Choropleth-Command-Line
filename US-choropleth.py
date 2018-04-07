import argparse
import pandas as pd
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import re
import os
import sys
from termcolor import colored
import numpy as np

matplotlib.rcParams['font.sans-serif'] = "Calibri"
matplotlib.rcParams['font.family'] = "sans-serif"
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['svg.fonttype'] = "none"

def set_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("data_file", type=str,
                            help="Path to the directory where your data set is living at.")

        parser.add_argument("-g", "--geometries", type=str,
                            choices=['state', 'county'],
                            help="Input `state` if you want to create a map at the state level or `county` if you want to create a map at the county level. If no argument is passed you will be prompted to input it later on. The geometry files for both levels live within the `data` directory.")

        parser.add_argument("-m", "--merge-on", type=str,
                            help="Specify a column name shared by the geometries file and your data set to merge them on. If the two files don't share a common column name, use `--merge-on-geometries` and `--merge-on-data` to specify the individual column names. If no argument is passed, you will be prompted to input it later on.")
        parser.add_argument("-mg", "--merge-on-geometries", type=str,
                            choices=['AP', 'FIPS', 'GPO', 'ISO_3166', 'USCG', 'USPS', 'fullname'],
                            help="Specify the column name from the geometries file you want to merge with your data file on. If no argument is passed you will be prompted to input it later on. For state-level map, you can use only `fullname`, `AP`, `FIPS`, `GPO`, `ISO_3166`, `USCG`, `USPS`. For county-level map only `fullname` and `FIPS`.")
        parser.add_argument("-md", "--merge-on-data", type=str,
                            help="Specify the column name from your data file you want to merge with the geometry file on. If no argument is passed you will be prompted to input it later on. Make sure the values in the data file column you merge on equal the values of the geometries file column, or else you risk missing rows or geopandas throwing an error.")

        parser.add_argument("-c", "--color-on", type=str,
                            help="Specify column name in your data file to color code the geometries (states or counties) on. If no argument passed you will be prompted to input it later on.")
        parser.add_argument("-cm", "--color-map", type=str,
                            choices=['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn', 'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper'],
                            help="Matplotlib sequential color maps to use for color coding. If no argument passed, it defaults to `Reds`. See all possible choices (Perceptually Uniform Sequential, Sequential 1 and 2) at: https://matplotlib.org/examples/color/colormaps_reference.html.")
        parser.add_argument("-cbl", "--colorbar-label", type=str,
                            help="Specify the label that will be used in the last bracket of the generated colorbar.")

        parser.add_argument("-p", "--projection", type=str,
                            help="Set your desired EPSG or ESRI projection. If no argument is passed, ESRI:102003 will be used. See possible EPSG and ESRI projections at: http://spatialreference.org/ref/epsg and at: http://spatialreference.org/ref/esri.")

        parser.add_argument("-t", "--title", type=str,
                            help="Set title for the map. If not specified the name of the data file will be used.")
        parser.add_argument("-ts", "--title-source", type=str,
                            help="Set source line. If not specified source line will return empty.")

        parser.add_argument("-e", "--extension", type=str,
                            choices=['png', 'pdf', 'svg'],
                            help="Export your map to .PNG, .PDF, or .SVG. If not specified, it defaults to .PNG.")
        parser.add_argument("-f", "--filename", type=str,
                            help="Set output filename. If not specified, the name of your data file will be used.")
        parser.add_argument("-o", "--open-with", action='store_true',
                            help="Flag to request opening the output map with the default program. If not used, opening the output will be suppressed.")

        return parser.parse_args()

def read_geom():
        print("Reading geometries file...")
        if not GEOM_FILE:
          print(colored("WARNING: You haven't specified the geometries you want to plot. You can pick between 'state' and 'county'.", "magenta"))
          geom_input = input(colored("WARNING: Enter the geometries you want to plot: ", "magenta"))
          if geom_input == 'state':
            geo_fname = './geometries/us_states.geojson'
            return gpd.read_file(geo_fname)
          elif geom_input == 'county':
            geo_fname = './geometries/us_counties.geojson'
            return gpd.read_file(geo_fname)
        else:
          if GEOM_FILE and GEOM_FILE == 'state':
            geo_fname = './geometries/us_states.geojson'
            return gpd.read_file(geo_fname)
          elif GEOM_FILE and GEOM_FILE == 'county':
            geo_fname = './geometries/us_counties.geojson'
            return gpd.read_file(geo_fname)

def read_data():
        print("Reading data file...")
        try:
          return pd.read_csv(DATA_FILE, dtype={'FIPS': 'str'})
        except UnicodeDecodeError:
          return pd.read_csv(DATA_FILE, dtype={'FIPS': 'str'}, encoding='iso-8859-1')

def merge_dfs(geom_df, data_df):
        print("Merging geometries with data...")
        geom_cols = list(geom_df.columns)
        df_cols = list(data_df.columns)
        cols_comm = [df_col for geom_col in geom_cols for df_col in df_cols if df_col == geom_col]

        if MERGE_ON:
          if MERGE_ON in geom_cols and MERGE_ON in df_cols:
            return geom_df.merge(data_df, on=MERGE_ON)
          elif MERGE_ON not in geom_cols or MERGE_ON not in df_cols:
            print(colored("WARNING: You're trying to merge on a column name that doesn't exist either in the geometries file or the data file.", "magenta"))
            if len(cols_comm) > 0:
              message = "Your geometries and data files have these columns in common you can merge on: " + str(cols_comm)
              print(colored(message, "magenta"))
              on_input = input(colored("WARNING: Enter exact name of the common column name you want to merge on: ", "magenta"))
              return geom_df.merge(data_df, on=on_input)
            else:
              print(colored("ERROR: Your geometries and data files have no columns in common to merge on. Please revise your data file. Exiting...", "red"))
              sys.exit()
        else:
          if MERGE_GEOM and MERGE_DATA:
            if MERGE_GEOM in geom_cols and MERGE_DATA in df_cols:
              return geom_df.merge(data_df, left_on=MERGE_GEOM, right_on=MERGE_DATA)
            elif MERGE_GEOM not in geom_cols or MERGE_DATA not in df_cols:
              print(colored("WARNING: You're trying to merge on a column name that doesn't exist either in the geometries file or the data file.", "magenta"))
              message = "The columns in your geometries file are: " + str(geom_cols)
              print(colored(message, "magenta"))
              left_input = input(colored("WARNING: Enter exact name of geometries file column name to merge on: ", "magenta"))
              message_ = "The columns in your data file are: " + str(df_cols)
              print(colored(message_, "magenta"))
              right_input = input(colored("WARNING: Enter exact name of data file column name to merge on: ", "magenta"))
              return geom_df.merge(data_df, left_on=left_input, right_on=right_input)
          elif not MERGE_GEOM or not MERGE_DATA:
              print(colored("WARNING: You haven't set column names to merge on for both the geometries and the data files.", "magenta"))
              message = "The columns in your geometries file are: " + str(geom_cols)
              print(colored(message, "magenta"))
              left_input = input(colored("WARNING: Enter exact name of geometries file column name to merge on: ", "magenta"))
              message_ = "The columns in your data file are: " + str(df_cols)
              print(colored(message_, "magenta"))
              right_input = input(colored("WARNING: Enter exact name of data file column name to merge on: ", "magenta"))
              return geom_df.merge(data_df, left_on=left_input, right_on=right_input)


def set_proj(proj_df):
        print("Setting projection...")
        if PROJ_CUSTOM:
          try:
            return proj_df.to_crs({'init': PROJ_CUSTOM})
          except RuntimeError:
            print(colored("WARNING: The requested projection doesn't exist. Try a different one or see all possible projections at: http://spatialreference.org/ref/epsg and at: http://spatialreference.org/ref/esri.", "magenta"))
            proj_input = input(colored("WARNING: Enter new projection: ", "magenta"))
            return proj_df.to_crs({'init': proj_input})
        else:
          return proj_df.to_crs({'init': 'ESRI:102003'})

def prepare_plot(plot_df):
        print("Preparing plot...")
        all_cols = list(plot_df.columns)

        if COLOR_COL:
          if COLOR_COL in all_cols:
            color_input = None
            col_to_color = COLOR_COL
          else:
            print(colored("WARNING: You're trying to color on a column that doesn't exist in your merged dataframe.", "magenta"))
            message = "The columns in your merged dataframe are: " + str(all_cols)
            print(colored(message, "magenta"))
            color_input = input(colored("WARNING: Enter exact name of column to color code: ", "magenta"))
            col_to_color = color_input
        else:
          color_input = input(colored("WARNING: Enter exact name of column to color code: ", "magenta"))
          if color_input in all_cols:
            col_to_color = color_input
          else:
            print(colored("WARNING: You're trying to color on a column that doesn't exist in your merged dataframe.", "magenta"))
            message = "The columns in your merged dataframe are: " + str(all_cols)
            print(colored(message, "magenta"))
            color_input = input(colored("WARNING: Enter exact name of column to color code: ", "magenta"))
            col_to_color = color_input

        if COLOR_MAP:
            cmap = COLOR_MAP
        else:
            cmap = "Reds"

        print("Please wait...")
        fig, ax = plt.subplots(figsize=(16, 12))
        plot_df.plot(ax=ax, cmap=cmap, column=col_to_color, edgecolor='white', linewidth=0.25)

        col_used = plot_df[col_to_color]
        col_min = col_used.min()
        col_max = col_used.max()
        norm = matplotlib.colors.Normalize(vmin=col_min, vmax=col_max)
        cb = matplotlib.colorbar.ColorbarBase(ax=ax, cmap=cmap, norm=norm, orientation='horizontal', alpha=0.8)

        cax = fig.add_axes([0.5, 0.1, 0.3, 0.01])
        cb._A = []
        cb = fig.colorbar(cb, cax=cax, orientation='horizontal', alpha=0.8)
        range_list = np.arange(col_min, col_max, (col_max / 5))
        range_list = np.append(range_list, col_max)
        cb.set_ticks(range_list)

        if COLOR_BAR:
          if COLOR_BAR == '%':
            cbar_label = COLOR_BAR
          else:
            cbar_label = ' ' + COLOR_BAR
        else:
          print(colored("WARNING: You haven't specified a data label for the map's colorbar.", "magenta"))
          cbar_input = input(colored("WARNING: Enter a data label: ", "magenta"))
          if cbar_input == '%':
            cbar_label = cbar_input
          else:
            cbar_label = ' ' + cbar_input

        cb.ax.set_xticklabels([str("{0:,.2f}".format(i)) + cbar_label if i == range_list[-1] else '0' if i == 0 else "{0:,.2f}".format(i) for i in range_list])

        if TITLE:
          map_title = TITLE
        else:
          if color_input:
            map_title_color = color_input
          else:
            map_title_color = COLOR_COL
          map_title = DATA_FILE.split('.csv')[0].split('/')[-1] + '-' + map_title_color
        ax.set_title(map_title, loc='left')

        if SOURCE:
          map_source = "Source: " + SOURCE
        else:
          map_source = "Source:"
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        ax.text(x=x_lims[0], y=y_lims[0] - (10 ** 5), s=map_source)

        ax.axis('off')
        print("Success.")

        if FILENAME:
          fname = re.sub(r'[ \@\!\#\$\%\^\&\*\(\)\[\]\{\}\_\+\=\<\>\,\.\?\/\\\|]', '-', FILENAME)
        else:
          replacing = DATA_FILE.split('.csv')[0].split('/')[-1]
          fname = re.sub(r'[ \@\!\#\$\%\^\&\*\(\)\[\]\{\}\_\+\=\<\>\,\.\?\/\\\|]', '-', replacing)
        if EXTENSION:
            print("Saving plot to " + EXTENSION.upper() + " ...")
            fname = fname + "." + EXTENSION
        else:
            print("Saving plot to PNG...")
            fname = fname + ".png"
        fname = "./outputs/" + fname
        plt.savefig(fname)
        return fname

def clean_svg(fname):
    if EXTENSION == 'svg':
        print("Cleaning SVG...")

        with open(fname, 'r') as file:
          filedata = file.read()

        filedata = re.sub(r'.*"patch_1"(.*)\n.*\n.*\n.*\n.*\n?.*?\n?.*?\n?.*?\n?.*?\n?.*?\n?.*?\n?.*?\n?.*?</g>', '', filedata)
        filedata = re.sub(r'clip(.*)" ', '', filedata)

        with open(fname, 'w') as file:
          file.write(filedata)
        print("Success.")

def open_file(fname):
    if OPEN_DEFAULT:
      print("Opening file with default program...")
      os.system("open " + fname)
      print("Success.")


args = set_args()
DATA_FILE = args.data_file
GEOM_FILE = args.geometries
MERGE_ON = args.merge_on
MERGE_GEOM = args.merge_on_geometries
MERGE_DATA = args.merge_on_data
PROJ_CUSTOM = args.projection
COLOR_COL = args.color_on
COLOR_MAP = args.color_map
COLOR_BAR = args.colorbar_label
EXTENSION = args.extension
TITLE = args.title
SOURCE = args.title_source
FILENAME = args.filename
OPEN_DEFAULT = args.open_with

gdf = read_geom()
print("Success.")
df = read_data()
print("Success.")
merged_df = merge_dfs(gdf, df)
print("Success.")
merged_df = set_proj(merged_df)
print("Success.")
file_name = prepare_plot(merged_df)
print("Success.")
clean_svg(file_name)
open_file(file_name)
