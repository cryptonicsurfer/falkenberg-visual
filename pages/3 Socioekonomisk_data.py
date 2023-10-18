import streamlit as st
import pandas as pd
import plotly.express as px
import json
from google.cloud import bigquery
from google.oauth2 import service_account

# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)

regsos = client.query('SELECT DISTINCT kommunnamn, lannamn, regsonamn, regso FROM `falkenbergcloud.scb_befolkning.dim_regso_deso`').to_dataframe()

# Fetch data from BigQuery into a pandas DataFrame
query = f'''
  SELECT
    *
  FROM `falkenbergcloud.scb_befolkning.regso_socio_halland` 
  '''
query_job = client.query(query)
df = query_job.to_dataframe()
df['andel_gymnasie_hogre_utbildning_20_64_ar'] = 100 - df['andel_forgymnasial_utbildning_20_64_ar']

# Fetch folkmängd data from BigQuery into a pandas DataFrame
query_folkmangd = f'''
  SELECT regso, ar, sum(folkmangd) as folkmangd
    
  FROM `falkenbergcloud.scb_befolkning.regso_folkmangd_halland`
  GROUP BY regso, ar
  '''
df_folkmangd = client.query(query_folkmangd).to_dataframe()


#merge dataframes
df = df.merge(regsos, on='regso', how='left')

df = df.merge(df_folkmangd, on=['regso', 'ar'], how='left')


#
latest_year = df['ar'].max()

#drop down for selecting kommun and storing it in a variable
# selected_kommun = st.selectbox('Välj kommun:',df['kommunnamn'].unique().tolist(), )

st.header('Socio-ekonomiska data för Falkenberg')
# valt_ar = st.selectbox('Välj år:', sorted(df['ar'].unique().tolist(), reverse=True))

st.subheader(f'Utbildning och ekonomisk utsatthet per område för {latest_year}')
# Define the refined column labels
column_label_map = {
    "socio_ek_index": "Socioekonomiskt Index",
    "socio_ek_nivå": "Socioekonomisk Nivå",
    "andel_forgymnasial_utbildning_20_64_ar": "Andel med Förgymnasial Utbildning (20-64 år)",
    "andel_lag_ekonomisk_standard": "Andel med Låg Ekonomisk Standard",
    "andel_ek_bistand_eller_langtidsarbetslos": "Andel med Ekonomiskt Bistånd eller Långtidsarbetslösa",
    "andel_gymnasie_hogre_utbildning_20_64_ar": "Andel av befolkningen 20-64 år med gymnasie- eller högre utbildning %"
}

#for choosing data variable to be displayed in the chart
#new dataframe for selections
df_selected = df[df['kommunnamn']=='Falkenberg'] # or selected_kommun] if variable 

selected_cols = df_selected.columns.tolist()[2:8]


fig = px.scatter(df_selected[df_selected['ar']==latest_year], 
                 x='andel_ek_bistand_eller_langtidsarbetslos',
                 y='andel_gymnasie_hogre_utbildning_20_64_ar',
                 size = df_selected[df_selected['ar']==latest_year]['folkmangd'].tolist(),
                 color='regsonamn',
                 text="regsonamn",
                 color_continuous_scale='teal',
                 labels={'andel_ek_bistand_eller_langtidsarbetslos':'Andel av befolkning 20-64 år med ekonomiskt bistånd och/eller långtidsarbetslösa, %', 'andel_gymnasie_hogre_utbildning_20_64_ar': 'Andel av befolkningen 20-64 år <br> med gymnasie- eller högre utbildning %',})
fig.update_layout(showlegend=False)
fig.update_traces(textposition="top center")
# Reverse the order of x and y axes
fig.update_xaxes(range=[8, 0])
# fig.update_yaxes(autorange="reversed")

fig.update_layout(
    xaxis=dict(
        title_font=dict(size=16),  # Adjust size as needed for x-axis title
        tickfont=dict(size=12)  # Adjust size as needed for x-axis tick labels
    ),
    yaxis=dict(
        title_font=dict(size=16),  # Adjust size as needed for y-axis title
        tickfont=dict(size=12)  # Adjust size as needed for y-axis tick labels
    )
)



st.write(fig)
st.write('Området Stafsinge-Gruebäcken har lägst andel med gymnasie- eller högre utbildning, samt högst andel ekonomiskt bistånd och/eller långtidsarbetslöshet')


st.write('---')

selected_variable = st.selectbox('Välj datapunkt', selected_cols, key='select1')





# Get the refined label for the selected variable
selected_variable_label = column_label_map[selected_variable]

line_fig = px.line(df_selected,
                   x='ar',
                   y=selected_variable,
                   line_group='regsonamn',
                   color='regsonamn',
                   labels={selected_variable: selected_variable_label}  # Set the refined y-label here
                   )

st.write(line_fig)

with st.expander('**För mer information om SCBs index och socioekonomiska variabler:**'):
  st.write('''Viktiga fotnoter

Delegationen mot segregation (Delmos) och Statistiska Centralbyrån (SCB) har utvecklat ett rikstäckande index som belyser hur olika områden förhåller sig till varandra avseende socioekonomisk status. Indexet baseras på Regionala statistikområden (RegSO) och relevanta statistiska indikatorer som vägs samman till ett sammanhållet index. Förutom indexet skapas områdestypsindelning som baseras på indexet. Delmos kommer att göra mer analyser på områdestyperna. För mer information och analyser besök Delmos hemsida på www.delmos.se Andel personer med låg ekonomisk standard baseras på undersökningen Inkomster och skatter . Från och med inkomståret 2011 inkluderas löne-och pensionsinkomster från nordiska länder och inkomster för hushåll tar hänsyn till växelvis boende. I samband med publicering av 2021 reviderades andel personer med låg ekonomisk standard, socioekonomiska indexet och områdestyper för åren 2011-2020. 2023-03-29: Tabellen är korrigerad. 2023-06-08: Tabellen är korrigerad för år 2011.
tabellinnehåll

Index
Det socioekonomiska indexet är ett sammanvägt index som baseras på tre indikatorer. Indikatorerna är: andel personer med låg ekonomisk standard (V1), andel personer med förgymnasial utbildning (V2) och andel personer som har haft ekonomiskt bistånd i minst tio månader och/eller har varit arbetslösa längre än sex månader (V3). Indexet beräknas sedan enligt (V1+V2+V3)/3. Notera att V1, V2 och V3 alla är kvoter omräknade till procent. Det innebär att de antar värden mellan 0 och 100 procent. Följaktligen kan indexet enbart anta värden mellan 0 och 100. Ju högre värde på indexet, desto sämre är de socioekonomiska förutsättningarna i ett RegSO. Ett värde på 100 innebär alltså att samtliga personer i ett RegSO har låg ekonomisk standard, att alla har förgymnasial utbildning (som högsta utbildningsnivå) samt att alla uppbär ekonomiskt bistånd och/eller har varit långtidsarbetslösa längre än sex månader. Förändringar i ett RegSO:s indexvärde från ett år till ett annat kommer att ske i samvariation med förändringar i de enskilda indikatorerna som ingår i indexet.

Vid analys av indexet över tid finns det flera saker att tänka på. Bland annat följande:
* Befolkningsstorleken skiljer sig mellan de olika RegSO. Detta kan påverka jämförelsen mellan olika RegSO:n.
* Det finns RegSO:n som domineras av en hög andel studenter på samma sätt som det finns RegSO:n som domineras av en hög andel pensionärer. Lägre inkomstnivå i dylika områden påverkar indexvärdet som räknas fram.
* I flera gränskommuner är medianinkomsten låg. En delförklaring till det är att många som bor i dessa kommuner jobbar på andra sidan gränsen. Inkomster som tjänas in utomlands inkluderas oftast inte i inkomststatistiken.
* Nybyggnation, ombyggnation eller annan omflyttning kan påverka områdets socioekonomiska status genom att påverka medelvärdet hos de i indexet ingående indikatorerna.

Förändringar i ett områdes socioekonomiska förutsättningar innebär att det alltid är viktig att undersöka orsaken till ett områdes eventuella förändring.

Det socioekonomiska indexet är utgångspunkten för klassificeringen av områdestyper.
Områdestyp
Områdestyp 1 – områden med stora socioekonomiska utmaningar
Områdestyp 2 – områden med socioekonomiska utmaningar
Områdestyp 3 – socioekonomiskt blandade områden
Områdestyp 4 – områden med goda socioekonomiska förutsättningar
Områdestyp 5 – områden med mycket goda socioekonomiska förutsättningar

Områdestyper är en klassificering av RegSO:n utifrån det socioekonomiska indexet. Syftet är att skapa en områdesindelning som beskriver de socioekonomiska förutsättningarna i ett RegSO. Områdesindelningen skapar därmed möjlighet att följa utvecklingen av olika områdestyper över tid, och även utvecklingen i olika RegSO:n över tid. Områdestyp 1 och områdestyp 2 går in under samlingsbegreppet områden med socioekonomiska utmaningar.

Områdestyperna baseras på hur många standardavvikelser från indexets medelvärde ett RegSO ligger. Standardavvikelse är ett mått på hur bred en fördelning är. Ju högre standardavvikelse, desto bredare fördelning. En låg standardavvikelse indikerar att indexvärdena för olika RegSO:n tenderar att ligga närmare indexets medelvärde. En hög standardavvikelse indikerar att indexvärdena för olika RegSO:n tenderar att ligga långt från indexets medelvärde, alltså att fördelningen av indexet är mer utspridd. Ju fler standardavvikelser över indexets medelvärde ett RegSO är, desto sämre socioekonomiska förutsättningar karaktäriseras RegSO:t av. Ju fler standardavvikelser under indexets medelvärde ett RegSO är, desto bättre socioekonomiska förutsättningar karaktäriseras RegSO:t av.
Andelen med förgymnasial utbildning (20-64 år)
Uppgiften om utbildningsnivå avser personens högsta utbildning. Utbildning klassificeras enligt Svensk utbildningsnomenklatur (SUN). Med förgymnasial utbildning avses förgymnasial utbildning nio år (motsvarande) och förgymnasial utbildning kortare än nio år. Populationen för denna indikator består av individer mellan 20–64 år och som var folkbokförda 31 december aktuellt år. I utbildningsregistret förekommer det bortfall där uppgifter om utbildningsnivå saknas vilket främst gäller utbildningar genomförda i utlandet. Detta innebär att en del individer tillskrivs en lägre utbildningsnivå än den faktiska. Täljaren består av antalet personer med förgymnasial utbildning i åldern 20-64 år. Nämnaren består av befolkningen 20-64 år.

Källa: SCB, STATIV
Andelen personer med låg ekonomisk standard (oavsett ålder)
Ekonomisk standard har hushållet som inkomstenhet och individen som analysenhet. Det betyder att alla hushållsmedlemmars disponibla inkomster summeras. Därefter justeras hushållets totala disponibla inkomst utifrån hushållets storlek och sammansättning och fördelas lika mellan hushållets medlemmar.
Disponibel inkomst är summan av alla skattepliktiga och skattefria inkomster minus skatt och övriga negativa transfereringar. Redovisningen är inklusive kapitalvinst/kapitalförlust, det vill säga den vinst/förlust som uppkommer vid försäljning (realisering) av tillgångar, t.ex. aktier, fonder eller fastigheter.

Låg ekonomisk standard avser andelen personer som lever i hushåll vars ekonomiska standard är mindre än 60 procent av medianvärdet för riket. Populationen består av samtliga individer som har varit folkbokförda både 1 januari och 31 december aktuellt år oavsett ålder. Det förekommer bortfall i inkomst- och taxeringsregistret. Detta då inte samtliga inkomster som intjänats i utlandet finns med. Detta påverkar främst gränskommuner där invånarna arbetar i ett annat land men är folkbokförda i kommunen.

Källa:
SCB, Inkomst- och taxeringsregistret (IoT)
Andelen med ekonomiskt bistånd och/eller långtidsarbetslösa (20-64 år)
Indikatorn är ett kombinerad indikator som avspeglar hur stor andel individer som antingen hade ekonomiskt bistånd i minst tio månader och/eller har varit arbetslösa längre än sex månader ett givet år.

Populationen för denna indikator består av individer mellan 20–64 år och som var folkbokförda 31 december aktuellt år.

Kommunerna redovisar varje år uppgifter om ekonomiskt bistånd till Socialstyrelsen. I inrapporteringen förekommer det dock bortfall vilket innebär att det för varje år finns kommuner som inte rapporterat in alla uppgifter om ekonomiskt bistånd. I syfte att hantera bortfallet ersätts ett genomsnittligt värde från närliggande års värden.

Källa: SCB, STATIV''')

