from collections import namedtuple
import altair as alt
import math
import geopandas as gpd
import pandas as pd
import numpy as np
import streamlit as st
import random
import time
import os
import SessionState
from PIL import Image
import pydeck as pdk

def get_session_state(rando):
    session_state = SessionState.get(random_number=random.random())
    return session_state

def cacherando():
    rando = random_number=random.random()
    return rando

def display_app_header(main_txt,sub_txt,is_sidebar = False):
    html_temp = f"""
    <h1 style = "color:black; text_align:left;"> {main_txt} </h2>
    <h2 style = "color:black; text_align:left;"> {sub_txt} </p>
    </div>
    """
    if is_sidebar:
        st.sidebar.markdown(html_temp, unsafe_allow_html = True)
    else: 
        st.markdown(html_temp, unsafe_allow_html = True)
        
def display_side_panel_header(txt):
    st.sidebar.markdown(f'## {txt}')

def main():
    st.set_page_config(page_title='Manhattan Urban Layout Analysis') #layout='wide', initial_sidebar_state='auto'
    rando = cacherando()
    session_state = get_session_state(rando)
    sep = '<|endoftext|>'
    main_txt = """🏙 Manhattan Urban Layout Analysis"""
    manhattan_clusters = pd.read_csv('data/manhattan_city_layouts.csv',index_col=0)
    df_tsne = pd.read_csv('data/city_tsne.csv',index_col=0)
    df_tsne.cluster = [str(int(c)) for c in df_tsne.cluster]
    geoNTA = pd.read_csv('data/geoNTA.csv',index_col=0)
    geoCluster = pd.read_csv('data/geoCluster.csv',index_col=0)
    
    ### SIDEBAR CONTENT ###
    display_side_panel_header("Planning Appliations")
    session_state.pages = st.sidebar.radio("Navigate different urban planning applications", 
                                           options=['Introduction','Classifying Urban Layout Typologies','Neighborhood Analysis','Generating Urban Layouts'])
    
    ### Introduction ###
    if session_state.pages == 'Introduction':
        sub_txt = "2021 NYU CUSP Capstone Project"
        display_app_header(main_txt,sub_txt,is_sidebar = False)
        
        st.write("Urban layouts are incredibly diverse and complex. Simple metrics like building footprint area \
                are incomplete in describing the higher-dimensional complexity and spatial hierarchy of these layouts. Other design language, \
                like 'urban grain' or 'morphology', are qualitative. Consensus on describing urban layouts or classifying them into meaningful \
                urban typologies is hard to come by.")

        st.write("This project is an attempt to describe urban layouts in a standardized, objective way by encoding their spatial structure using \
                deep neural networks. We show how their encoded latent features can be used in downstream urban planning applications, including \
                neigborhood analysis and generating composite urban layouts.")
        
    ### Classifying Urban Layout Typologies ###
    if session_state.pages == 'Classifying Urban Layout Typologies':
        sub_txt = "Classifying Urban Layout Typologies"
        display_app_header(main_txt,sub_txt,is_sidebar = False)
        
        st.write("Using the AETree autoencoder, we extracted the latent features of each Manhattan urban layout and \
                 performed dimensionality reduction using Principal Component Analysis (PCA). Using Gaussian Mixture Models (GMM) clustering algorithm, \
                 we found 11 urban layout typologies that describe the Manhattan style.")
        st.write("The plot below is constructed using a t-distributed stochastic neighbor embedding (t-SNE), \
                 which faithfully represents the higher-dimensional layouts in a 2D-space.")
        
        clusterSelect = st.multiselect('Select cluster(s) to view:',options=[str(c) for c in range(11)],default=[str(c) for c in range(11)])
        c = alt.Chart(df_tsne, height=600).mark_circle(size=10).encode(x='Dim1', y='Dim2',
                                                                color='cluster', 
                                                                tooltip=['area','perimeter','std_area','std_perimeter','avg_lw','avg_rot','std_rot']).transform_filter(
            alt.FieldOneOfPredicate(field='cluster', oneOf=clusterSelect))
        st.altair_chart(c, use_container_width=True)
        
        # cluster geometry features
        st.subheader("Geometric statistics")
        st.write("Geometric statistics were tabulated for each cluster, revealing that the clusters \
                likely represent unique urban layout typologies that define the Manhattan cityscape.")
        st.write(geoCluster.iloc[:,:7])
        
        st.write("")
        st.write("Based on these geometry features, we can assign descriptive labels to each cluster which are key considerations for urban planning.")
        """
        * **Building Density**: proportion of layout covered by building footprints
        * **Building Regularity**: average elongation of buildings, or length:width ratio
        * **Evenness**: size and shape similarity of buildings
        """
        st.write(geoCluster.iloc[:,7:])


    ### Neighborhood Analysis ###
    if session_state.pages == 'Neighborhood Analysis':
        sub_txt = "Neighborhood Analysis"
        display_app_header(main_txt,sub_txt,is_sidebar = False)
        NTA_GMM = gpd.read_file('https://raw.githubusercontent.com/lazfishing/manhattan-city-layouts/master/data/manhattan_nta.geojson')
        display_side_panel_header("Configuration")
        session_state.viz_setting = st.sidebar.radio("Settings for visualization", options=['Original metric for layout diversity','Deviation from Manhattan baseline'])

        st.write("Each Manhattan Neighborhood Tabulation Area (NTA) contains a tremendous diversity of urban layouts - \
                from grid patterns to coarse urban grains. We constructed a neighborhood geomtery 'profile' for each NTA, which considers the percentage \
                composition of urban layouts by GMM cluster (derived using the latent space of each urban layout).")
        st.write("A standard, objective metric for geometry profiling can be obtained by reducing this multi-dimensional profile using PCA. We can also \
                calculate the deviation of each neighborhood profile from the city baseline. Both perspectives are visualized on this map.")
        
        PCALayer =  pdk.Layer(
            "GeoJsonLayer",
            NTA_GMM,
            opacity=0.6,
            stroked=True,
            filled=True,
            get_fill_color='[gmm_pca_color, 255-gmm_pca_color, 255-gmm_pca_color]',
            auto_highlight=True,
            pickable=True)
        
        DeviationLayer =  pdk.Layer(
            "GeoJsonLayer",
            NTA_GMM,
            opacity=0.6,
            stroked=True,
            filled=True,
            get_fill_color='[deviation * 0.5 * 255, deviation * 255, deviation * 0.5 * 255]',
            auto_highlight=True,
            pickable=True)
        
        tooltip = {
            "html": "<b>{ntaname}</b> </br>Standard metric for layout diversity: {gmm_pca} </br>Normalized deviation from Manhattan baseline: {deviation}", 
            "style": {
                "backgroundColor": "black", 
                "color": "white", 
                "font-size": "12px"
            }}
        
        if session_state.viz_setting == 'Original metric for layout diversity':
            layers = [PCALayer]
        else:
            layers = [DeviationLayer]
                    
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=40.7751,
                longitude=-73.9512,
                zoom=10.2,
                pitch=35,
                height=400,
            ),
            layers=layers,
            tooltip=tooltip
        ))
        
        st.write("")
        st.subheader("Neighborhood Layout Analysis")
        st.write("Take a closer look at the neighborhood geometry profile for each Manhattan NTA.")
        neighborhood = st.selectbox('Select a neighborhood to view', options=manhattan_clusters.nta.unique())
        nhood = list(manhattan_clusters.nta.unique()).index(neighborhood)
        nta_profile = manhattan_clusters[manhattan_clusters.nta==neighborhood]
        total_buildings = len(nta_profile)

        st.markdown("**Geometric profile of {}**".format(neighborhood))
        st.write('The geometry values are expressed in standardized units and are useful for comparing against the Manhattan baseline.')
        geometry_df = geoNTA[geoNTA.index.isin([neighborhood,'Manhattan'])].T
        st.write(geometry_df)
                                                               
        st.write("")
        st.write("")
        col1, col2 = st.beta_columns([3,2])
            
        with col1:
            dev_count = []
            total_man_buildings = len(manhattan_clusters)
            for i in range(11):
                total_count = (len(manhattan_clusters[manhattan_clusters.gmm==i])/total_man_buildings)
                dev_count.append(round(((len(nta_profile[nta_profile.gmm==i])/total_buildings)/total_count)-1,3))
                
            dev_count_df = pd.DataFrame(data=zip(list(range(11)),dev_count),columns=['cluster','deviation'])

            c2 = alt.Chart(dev_count_df,title='Deviation from Manhattan style by cluster').mark_bar(size=12).encode(
                x='cluster',
                y=alt.Y('deviation',
                      scale = alt.Scale(domain=(-1, 1))),
                tooltip=['deviation'],
            )

            st.altair_chart(c2,use_container_width=True)
            
        with col2:
            image = Image.open('indiv_layouts/{}.png'.format(nhood))
            st.image(image, caption='City layout extracted from {}'.format(neighborhood))

        st.write("")
        gmm_count = []
        for i in range(11):
            gmm_count.append(round(len(nta_profile[nta_profile.gmm==i])/total_buildings,3))
        gmm_count_df = pd.DataFrame(data=zip(list(range(11)),gmm_count),columns=['cluster','%layouts'])

        c1 = alt.Chart(gmm_count_df,title='Percentage composition by cluster').mark_bar(size=20).encode(
            x='cluster',
            y=alt.Y('%layouts',
                    scale = alt.Scale(domain=(0,0.35))),
            tooltip=['%layouts'],
        )

        st.altair_chart(c1,use_container_width=True)

    ### Blending Urban Layouts ###
    if session_state.pages == 'Generating Urban Layouts':
        sub_txt = "Generating Urban Layouts"
        display_app_header(main_txt,sub_txt,is_sidebar = False)
        display_side_panel_header("Configuration")
        session_state.interpolate_setting = st.sidebar.radio("Settings for latent interpolation",options=['Overview','Individual transitions'],
                                                            help="Select 'Overview' to see the complete set of blending transitions. \
                                                            Select 'Individual transitions' to view each blended layout individually.")
        list1 = ['SoHo-TriBeCa-Civic Center-Little Italy','East Harlem North','Clinton','Upper West Side']
        list2 = ['Chinatown','Battery Park City-Lower Manhattan','Manhattanville','Stuyvesant Town-Cooper Village']
        nta_A = st.sidebar.selectbox('Neighborhood A', options=list1)
        nta_B = st.sidebar.selectbox('Neighborhood B', options=list2)
        A = [1,4,5,6][list1.index(nta_A)]
        B = 28 - [19,21,25,28][list2.index(nta_B)]
        
        st.write("The linearly interpolated values of two distinct latent spaces can be decoded using AETree to generate new urban layouts \
                that bear resemblance to both original layouts. This could be useful for rapidly generating new urban designs \
                based on real-world urban layouts, especially in redevelopment projects where the surrounding urban design is an important consideration.")
        
        if session_state.interpolate_setting == 'Overview':
            image = Image.open('set_interpolate/{}_{}.png'.format(A,B))
            st.image(image, caption='Blending of {} and {} urban layouts'.format(nta_A,nta_B))
            
        else:
            latent_num = st.slider('Drag the slider to see blending! Please be patient while the layouts load...',1,12)
            image = Image.open('interpolation/{}_{}_{}.png'.format(A,B,latent_num-1))
            st.image(image, caption='Blending of {} and {} urban layouts'.format(nta_A,nta_B))
                
if __name__ == "__main__":
    main()
