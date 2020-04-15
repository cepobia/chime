"""App."""

import os

import altair as alt  # type: ignore
import streamlit as st  # type: ignore

from penn_chime.parameters import Parameters
from penn_chime.presentation import (
    display_download_link,
    display_footer,
    display_header,
    display_sidebar,
    hide_menu_style,
)
from penn_chime.models import SimSirModel
from penn_chime.charts import (
    build_admits_chart,
    build_census_chart,
    build_sim_sir_w_date_chart,
)

# This is somewhat dangerous:
# Hide the main menu with "Rerun", "run on Save", "clear cache", and "record a screencast"
# This should not be hidden in prod, but removed
# In dev, this should be shown
st.markdown(hide_menu_style, unsafe_allow_html=True)

d = Parameters.create(os.environ, [])
p = display_sidebar(st, d)
m = SimSirModel(p)

display_header(st, m, p)

st.subheader("Nuevas Admisiones")
st.markdown("Número proyectado de admisiones ** COVID-19 ** diarias.")
admits_chart = build_admits_chart(alt=alt, admits_floor_df=m.admits_floor_df, max_y_axis=p.max_y_axis)
st.altair_chart(admits_chart, use_container_width=True)
display_download_link(
    st,
    filename=f"{p.current_date}_projected_admits.csv",
    df=m.admits_df,
)

st.subheader("Pacientes admitidos (Censo)")
st.markdown("Proyectado ** censo ** de pacientes con COVID-19, contabilizando llegadas y altas.")
census_chart = build_census_chart(alt=alt, census_floor_df=m.census_floor_df, max_y_axis=p.max_y_axis)
st.altair_chart(census_chart, use_container_width=True)
display_download_link(
    st,
    filename=f"{p.current_date}_projected_census.csv",
    df=m.census_df,
)

st.subheader("Susceptible, infectado y recuperado")
st.markdown("El número de individuos susceptibles, infectados y recuperados en la región de captación del hospital en un momento dado")
sim_sir_w_date_chart = build_sim_sir_w_date_chart(alt=alt, sim_sir_w_date_floor_df=m.sim_sir_w_date_floor_df)
st.altair_chart(sim_sir_w_date_chart, use_container_width=True)
display_download_link(
    st,
    filename=f"{p.current_date}_sim_sir_w_date.csv",
    df=m.sim_sir_w_date_df,
)

display_footer(st)
