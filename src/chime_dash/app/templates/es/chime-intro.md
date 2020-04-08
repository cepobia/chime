# CHIME
### Una herramienta para la planificación de capacidad Hospitalaria - COVID-19

Mientras nos preparamos para las demandas adicionales que el COVID-19
brote se colocará en nuestro sistema hospitalario, nuestro operativo
los líderes necesitan proyecciones actualizadas de qué recursos adicionales
será requerido. Estimaciones informadas de cuántos pacientes
necesita hospitalización, camas de UCI y ventilación mecánica sobre
los próximos días y semanas serán aportes cruciales para las respuestas de preparación
y estrategias de mitigación.

CHIME permite a los hospitales ingresar información sobre su población y modificar las suposiciones sobre la propagación y el comportamiento de COVID-19. Luego ejecuta un modelo SIR estándar para proyectar la cantidad de ingresos hospitalarios nuevos cada día, junto con el censo diario del hospital. Estas proyecciones se pueden utilizar para crear los mejores y peores escenarios para ayudar con la planificación de la capacidad. Anunciamos hoy que somos CHIME de código abierto y lo ponemos a disposición de la comunidad sanitaria.

Si bien los parámetros predeterminados se personalizan y actualizan continuamente para reflejar la situación en Penn Medicine, CHIME se puede adaptar para que lo use cualquier sistema hospitalario modificando los parámetros para reflejar los contextos locales.

El parámetro más impactante en un modelo SIR es el tiempo de duplicación. Este parámetro define qué tan rápido se propaga una enfermedad. Las experiencias en otros contextos geográficos sugieren que el tiempo de duplicación puede variar de 3 a 13 días o más, con ejemplos notables:

Wuhan, China: 6 días
Corea del Sur: 13 días (a partir del 14 de marzo de 2020)
Italia: 5 días (a partir del 14 de marzo de 2020)
Este valor es particularmente importante debido a la naturaleza exponencial de la propagación de enfermedades infecciosas como COVID-19. Esta es también la razón por la cual los funcionarios de salud pública recomiendan medidas como el distanciamiento social y el lavado de manos: cuanto más podamos frenar la propagación de COVID-19, menor será la demanda máxima en nuestro sistema de salud. Pruebe nuestra versión en vivo de CHIME y vea qué sucede cuando modifica el parámetro Doubling Time. También puede experimentar con escenarios que involucran diferentes niveles de severidad de incidencia y períodos de estadía promedio para cada clase de severidad.

Nos hemos esforzado por determinar buenas estimaciones para todos los parámetros del modelo y hemos establecido los valores predeterminados en consecuencia. Algunos de los valores predeterminados se basan en la situación actual en nuestra región natal de Filadelfia. Si está trabajando en algún lugar fuera de la región de Filadelfia, simplemente puede modificar los siguientes parámetros para adaptarse a su población de pacientes:

Infecciones regionales actualmente conocidas
Pacientes hospitalizados actualmente con COVID-19
Cuota de mercado hospitalaria (%)
A medida que avanza la propagación local, se pueden hacer estimaciones revisadas para algunos de los valores en CHIME. Haremos todo lo posible para mantener las cosas actualizadas con las últimas investigaciones, pero si encuentra algún problema con alguno de los valores que estamos utilizando, apreciaremos sus comentarios y contribuciones. También configuramos un canal de Slack si desea chatear con nosotros.

- Penn Predictive Healthcare Team