"""effectful functions for streamlit io"""

from typing import Optional
from datetime import date

import altair as alt
import numpy as np
import os
import json
import pandas as pd
import penn_chime.spreadsheet as sp
from .constants import (
    CHANGE_DATE,
    DOCS_URL,
    EPSILON,
    FLOAT_INPUT_MIN,
    FLOAT_INPUT_STEP,
    VERSION,
)

from .utils import dataframe_to_base64
from .parameters import Parameters, Disposition
from .models import SimSirModel as Model

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """


########
# Text #
########


def display_header(st, m, p):

    infected_population_warning_str = (
        """(Advertencia: El número de infecciones estimadas es mayor que la población regional total. Verifique los valores ingresados en la barra lateral.)"""
        if m.infected > p.population
        else ""
    )

    st.markdown(
        """
<link rel="stylesheet" href="https://www1.pennmedicine.org/styles/shared/penn-medicine-header.css">
<div class="penn-medicine-header__content">
    <img src="https://cepobia.com/assets/images/logos/simbolo.png"  alt="cepobia" style="width:30px;height:30px;">
    <a id="title" class="penn-medicine-header__title">Biapp - Modelo Impacto Hospitalario (CHIME)</a>
</div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """**Aviso**: *Existe un alto grado de incertidumbre sobre los detalles de la infección, transmisión 
        y la efectividad de las medidas de distanciamiento social de COVID-19. Las proyecciones a largo plazo
         realizadas con este modelo simplificado de progresión del brote deben tratarse con extrema precaución.*
    """
    )
    st.markdown(
        """
            Esta [Biapp](https://cepobia.com/BIaaS/) fue desarrollada por [Cepobia](https://cepobia.com/) y 
            se basa en el trabajo puesto a disposición de forma gratuita (bajo licencia MIT) por Penn Medicine [Predictive Healthcare team](http://predictivehealthcare.pennmedicine.org/).
            Para ayudar a hospitales y funcionarios de salud publica con la planificacion de la capacidad hospitalaria"""
    )
    st.markdown(
        """ # Resultados
El numero estimado de individuos actualmente infectados es de **{total_infections:.0f}**. Esto se basa en las entradas actuales para hospitalizaciones. (**{current_hosp}**), Tasa de hospitalizacion (**{hosp_rate:.0%}**), Poblacion regional (**{S}**),
y cuota de mercado del hospital (**{market_share:.0%}**).
{infected_population_warning_str}

Un tiempo de duplicacion inicial de **{doubling_time}** dias y un tiempo de recuperacion de **{recovery_days}** dias que implican un **`R0`** de
**{r_naught:.2f}** y tasa de crecimiento diario de **{daily_growth:.2f}%**.

**Mitigación**: Una reduccion del **{relative_contact_rate:.0%}**  en el contacto social despues del inicio del brote **{impact_statement:s} {doubling_time_t:.1f}** dias, lo que implica un efectivo **`R(t)`** de **{r_t:.2f}**
y una tasa de crecimiento diario de **{daily_growth_t:.2f}%**.
""".format(
            total_infections=m.infected,
            current_hosp=p.current_hospitalized,
            hosp_rate=p.hospitalized.rate,
            S=p.population,
            market_share=p.market_share,
            recovery_days=p.infectious_days,
            r_naught=m.r_naught,
            doubling_time=p.doubling_time,
            relative_contact_rate=p.relative_contact_rate,
            r_t=m.r_t,
            doubling_time_t=abs(m.doubling_time_t),
            impact_statement=(
                "halves the infections every"
                if m.r_t < 1
                else "reduces the doubling time to"
            ),
            daily_growth=m.daily_growth_rate * 100.0,
            daily_growth_t=m.daily_growth_rate_t * 100.0,
            infected_population_warning_str=infected_population_warning_str,
        )
    )

    return None


class Input:
    """Helper to separate Streamlit input definition from creation/rendering"""

    def __init__(self, st_obj, label, value, kwargs):
        self.st_obj = st_obj
        self.label = label
        self.value = value
        self.kwargs = kwargs

    def __call__(self):
        return self.st_obj(self.label, value=self.value, **self.kwargs)


class NumberInput(Input):
    def __init__(
        self,
        st_obj,
        label,
        min_value=None,
        max_value=None,
        value=None,
        step=None,
        format=None,
        key=None,
    ):
        kwargs = dict(
            min_value=min_value, max_value=max_value, step=step, format=format, key=key
        )
        super().__init__(st_obj.number_input, label, value, kwargs)


class DateInput(Input):
    def __init__(self, st_obj, label, value=None, key=None):
        kwargs = dict(key=key)
        super().__init__(st_obj.date_input, label, value, kwargs)


class PercentInput(NumberInput):
    def __init__(
        self,
        st_obj,
        label,
        min_value=0.0,
        max_value=100.0,
        value=None,
        step=FLOAT_INPUT_STEP,
        format="%f",
        key=None,
    ):
        super().__init__(
            st_obj, label, min_value, max_value, value * 100.0, step, format, key
        )

    def __call__(self):
        return super().__call__() / 100.0


class CheckboxInput(Input):
    def __init__(self, st_obj, label, value=None, key=None):
        kwargs = dict(key=key)
        super().__init__(st_obj.checkbox, label, value, kwargs)


def display_sidebar(st, d: Parameters) -> Parameters:
    # Initialize variables
    # these functions create input elements and bind the values they are set to
    # to the variables they are set equal to
    # it's kindof like ember or angular if you are familiar with those

    st_obj = st.sidebar
    # used_widget_key = st.get_last_used_widget_key ( )

    current_hospitalized_input = NumberInput(
        st_obj,
        " Pacientes Actualmente Hospitalizados con Covid-19",
        min_value=0,
        value=d.current_hospitalized,
        step=1,
        format="%i",
    )
    n_days_input = NumberInput(
        st_obj,
        "Número de dias para proyectar",
        min_value=30,
        value=d.n_days,
        step=1,
        format="%i",
    )
    doubling_time_input = NumberInput(
        st_obj,
        "Tiempo de duplicacion en dias (hasta hoy. Esto sobrescribe la fecha de la primera estimacion hospitalizada)",
        min_value=0.5,
        value=d.doubling_time,
        step=0.25,
        format="%f",
    )
    current_date_input = DateInput(
        st_obj, "Fecha actual (el valor predeterminado es hoy)", value=d.current_date,
    )
    date_first_hospitalized_input = DateInput(
        st_obj, "Fecha del primer caso hospitalizado (ingrese esta fecha para que CHIME calculé el tiempo de duplicación inicial)",
        value=d.date_first_hospitalized,
    )
    mitigation_date_input = DateInput(
        st_obj, "Fecha de efecto de las medidas de distanciamiento social (puede retrasarse su implementación)",
        value=d.mitigation_date
    )
    relative_contact_pct_input = PercentInput(
        st_obj,
        "Distanciamiento social (% de reducción en el contacto social en el futuro)",
        min_value=0.0,
        max_value=100.0,
        value=d.relative_contact_rate,
        step=1.0,
    )
    hospitalized_pct_input = PercentInput(
        st_obj,
        "Tasa de hospitalización (% del total de infecciones)",
        value=d.hospitalized.rate,
        min_value=FLOAT_INPUT_MIN,
        max_value=100.0
    )
    icu_pct_input = PercentInput(st_obj,
        "Tasa UCI (% del total de infecciones)",
        min_value=0.0,
        value=d.icu.rate,
        step=0.05
    )
    ventilated_pct_input = PercentInput(
        st_obj, "Tasa Ventilados (% del total de infecciones)", value=d.ventilated.rate,
    )
    hospitalized_days_input = NumberInput(
        st_obj,
        "Estancia promedio de la hospitalización (en dias)",
        min_value=1,
        value=d.hospitalized.days,
        step=1,
        format="%i",
    )
    icu_days_input = NumberInput(
        st_obj,
        "Promedio de dias en UCI",
        min_value=1,
        value=d.icu.days,
        step=1,
        format="%i",
    )
    ventilated_days_input = NumberInput(
        st_obj,
        "Promedio de dias con ventilación",
        min_value=1,
        value=d.ventilated.days,
        step=1,
        format="%i",
    )
    market_share_pct_input = PercentInput(
        st_obj,
        "Mercado del Hospital (%)",
        min_value=0.5,
        value=d.market_share,
    )
    population_input = NumberInput(
        st_obj,
        "Población Ciudad",
        min_value=1,
        value=(d.population),
        step=1,
        format="%i",
    )
    infectious_days_input = NumberInput(
        st_obj,
        "Dias infecciosos",
        min_value=1,
        value=d.infectious_days,
        step=1,
        format="%i",
    )
    max_y_axis_set_input = CheckboxInput(
        st_obj, "Fije el eje Y en los gráficos"
    )
    max_y_axis_input = NumberInput(
        st_obj, "Valor estático del eje Y", value=500, format="%i", step=25
    )

    # Build in desired order
    st.sidebar.markdown(
        """**CHIME [{version}](https://github.com/CodeForPhilly/chime/releases/tag/{version}) ({change_date})**""".format(
            change_date=CHANGE_DATE,
            version=VERSION,
        )
    )

    st.sidebar.markdown(
        "### Parámetros del Hospital [ℹ]({docs_url}/what-is-chime/parameters#hospital-parameters)".format(
            docs_url=DOCS_URL
        )
    )
    population = population_input()
    market_share = market_share_pct_input()
    # known_infected = known_infected_input()
    current_hospitalized = current_hospitalized_input()

    st.sidebar.markdown(
        "### Parámetros de propagación y contacto [ℹ]({docs_url}/what-is-chime/parameters#spread-and-contact-parameters)".format(
            docs_url=DOCS_URL
        )
    )

    if st.sidebar.checkbox(
        "Sé la fecha del primer caso hospitalizado."
    ):
        date_first_hospitalized = date_first_hospitalized_input()
        doubling_time = None
    else:
        doubling_time = doubling_time_input()
        date_first_hospitalized = None

    if st.sidebar.checkbox(
        "Se han implementado medidas de distanciamiento social.",
        value=(d.relative_contact_rate > EPSILON)
    ):
        mitigation_date = mitigation_date_input()
        relative_contact_rate = relative_contact_pct_input()
    else:
        mitigation_date = None
        relative_contact_rate = EPSILON

    st.sidebar.markdown(
        "### Parámetros de Severidad[ℹ]({docs_url}/what-is-chime/parameters#severity-parameters)".format(
            docs_url=DOCS_URL
        )
    )
    hospitalized_rate = hospitalized_pct_input()
    icu_rate = icu_pct_input()
    ventilated_rate = ventilated_pct_input()
    infectious_days = infectious_days_input()
    hospitalized_days = hospitalized_days_input()
    icu_days = icu_days_input()
    ventilated_days = ventilated_days_input()

    st.sidebar.markdown(
        "### Parámetros de Visualización [ℹ]({docs_url}/what-is-chime/parameters#display-parameters)".format(
            docs_url=DOCS_URL
        )
    )
    n_days = n_days_input()
    max_y_axis_set = max_y_axis_set_input()

    max_y_axis = None
    if max_y_axis_set:
        max_y_axis = max_y_axis_input()

    current_date = current_date_input()
    #Subscribe implementation
    #subscribe(st_obj)

    return Parameters(
        current_hospitalized=current_hospitalized,
        current_date=current_date,
        date_first_hospitalized=date_first_hospitalized,
        doubling_time=doubling_time,
        hospitalized=Disposition.create(
            rate=hospitalized_rate,
            days=hospitalized_days),
        icu=Disposition.create(
            rate=icu_rate,
            days=icu_days),
        infectious_days=infectious_days,
        market_share=market_share,
        max_y_axis=max_y_axis,
        mitigation_date=mitigation_date,
        n_days=n_days,
        population=population,
        recovered=d.recovered,
        relative_contact_rate=relative_contact_rate,
        ventilated=Disposition.create(
            rate=ventilated_rate,
            days=ventilated_days),
    )

#Read the environment variables and cteate json key object to use with ServiceAccountCredentials
def readGoogleApiSecrets():
    client_secret = {}
    os.getenv
    type = os.getenv ('GAPI_CRED_TYPE').strip()
    print (type)
    client_secret['type'] = type,
    client_secret['project_id'] = os.getenv ('GAPI_CRED_PROJECT_ID'),
    client_secret['private_key_id'] = os.getenv ('GAPI_CRED_PRIVATE_KEY_ID'),
    client_secret['private_key'] = os.getenv ('GAPI_CRED_PRIVATE_KEY'),
    client_secret['client_email'] = os.getenv ('GAPI_CRED_CLIENT_EMAIL'),
    client_secret['client_id'] = os.getenv ('GAPI_CRED_CLIENT_ID'),
    client_secret['auth_uri'] = os.getenv ('GAPI_CRED_AUTH_URI'),
    client_secret['token_uri'] = os.getenv ('GAPI_CRED_TOKEN_URI'),
    client_secret['auth_provider_x509_cert_url'] =  os.getenv ('GAPI_CRED_AUTH_PROVIDER_X509_CERT_URL'),
    client_secret['client_x509_cert_url'] = os.getenv ('GAPI_CRED_CLIENT_X509_CERT_URI'),
    json_data = json.dumps (client_secret)
    print(json_data)
    return json_data

def readGoogleApiSecretsDict():
    type = os.getenv ('GAPI_CRED_TYPE')
    project_id = os.getenv ('GAPI_CRED_PROJECT_ID')
    private_key_id =  os.getenv ('GAPI_CRED_PRIVATE_KEY_ID')
    private_key = os.getenv ('GAPI_CRED_PRIVATE_KEY')
    client_email = os.getenv ('GAPI_CRED_CLIENT_EMAIL')
    client_id = os.getenv ('GAPI_CRED_CLIENT_ID')
    auth_uri = os.getenv ('GAPI_CRED_AUTH_URI')
    token_uri = os.getenv ('GAPI_CRED_TOKEN_URI')
    auth_provider_x509_cert_url = os.getenv ('GAPI_CRED_AUTH_PROVIDER_X509_CERT_URL')
    client_x509_cert_url = os.getenv ('GAPI_CRED_CLIENT_X509_CERT_URI')

    secret = {
        'type' : type,
        'project_id' : project_id,
        'private_key_id' : private_key_id,
        'private_key':private_key,
        'client_email': client_email,
        'client_id': client_id,
        'auth_uri': auth_uri,
        'token_uri': token_uri,
        'auth_provider_x509_cert_url':auth_provider_x509_cert_url,
        'client_x509_cert_url':client_x509_cert_url
    }
    return secret

def subscribe(st_obj):
    st_obj.subheader ("Subscribe")
    email = st_obj.text_input (label="Enter Email", value="", key="na_lower_1")
    name = st_obj.text_input (label="Enter Name", value="", key="na_upper_1")
    affiliation = st_obj.text_input (label="Enter Affiliation", value="", key="na_upper_2")
    if st_obj.button (label="Submit", key="ta_submit_1"):
        row = [email, name, affiliation]
        send_subscription_to_google_sheet(st_obj, row)

def send_subscription_to_google_sheet(st_obj, row):
    json_secret = readGoogleApiSecretsDict()
    #print(json_secret)
    spr = sp.spreadsheet (st_obj, json_secret)
    spr.writeToSheet("CHIME Form Submissions", row)

def display_footer(st):
    st.subheader("Agradecimientos")
    st.markdown(
        """* Nos gustaria agradecer [Code for Philly](https://codeforphilly.org/) y los muchos miembros de la comunidad de codigo abierto que [contribuyeron](https://github.com/CodeForPhilly/chime/graphs/contributors) en este Proyecto.
    """
    )
    st.markdown("© 2020, CepoBIA")


def display_download_link(st, filename: str, df: pd.DataFrame):
    csv = dataframe_to_base64(df)
    st.markdown(
        """
        <a download="{filename}" href="data:file/csv;base64,{csv}">Download {filename}</a>
""".format(
            csv=csv, filename=filename
        ),
        unsafe_allow_html=True,
    )
