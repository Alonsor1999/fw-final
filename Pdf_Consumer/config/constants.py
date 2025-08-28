import re
import unicodedata

# =============== Normalización de texto =================

def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def _norm_phrase(s: str) -> str:
    s = _strip_accents(s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ===================== Constantes / filtros =====================

CONNECTORS = {"de","del","la","las","los","y","da","do","das","dos"}

INSTITUTION_NOISE = {
    "REPUBLICA","COLOMBIA","REGISTRADURIA","NACIONAL","ESTADO","CIVIL","RAMA","JUDICIAL",
    "MINISTERIO","DIRECCION","SECRETARIA","GOBIERNO","FORMULARIO","CERTIFICADO","DOCUMENTO",
    "RADICADO","CONSULTA","WEB","NIT","DPI","ID","CC","C.C","C.C.","RESOLUCION","OFICIO",
    "ACTA","MUNICIPAL","DEPARTAMENTO","NRO","N°","NO","Nº","N"
}

# Palabras “tóxicas” para que el barredor no tome encabezados/lugares/roles
DISQUALIFY_TERMS = {
    "SECCION","INVESTIGACIONES","POLICIA","JUDICIAL","CTI","FISCALIA","CORTE","SUPREMA",
    "JUSTICIA","SALA","CASACION","MAGISTRADO","MAGISTRADA","DOCTOR","DOCTORA",
    "JEFE","JEFA","LIDER","GRUPO","PROFESIONAL","INVESTIGADOR","INVESTIGADORA",
    "SOLICITUD","INFORMACION","REFERENCIA","ASUNTO","RESPECTO","RESPECTADO","CIUDAD",
    "NACIONAL","REGISTRADURIA","OFICINA","JURIDICA","NOMBRE",
    "RECTOR","RECTORA","DEFENSOR","DEFENSORA","CURA","PARROCO","PÁRROCO",
    "COORDINADOR","COORDINADORA",
    "PRIMER APELLIDO", "NORTE DE SANTANDER", "LUGAR DE NACIMIENTO", "SEGUNDO APELLIDO", "NÚMERO DESPACHO"
}

# Palabras comunes que NO son nombres (para el barredor genérico)
NON_NAME_COMMON = {
    "CADA","UNO","UNA","UNOS","UNAS","ELLOS","ELLAS","ESTE","ESTA","ESTOS","ESTAS",
    "ESE","ESA","ESOS","ESAS","AQUEL","AQUELLA","AQUELLOS","AQUELLAS",
    "ESPECIFICANDO","ESPECIFICACION","DETALLE","DETALLES","DOCUMENTACION"
}

BLACKLIST_TOKENS = {
    "OCR", "PÁGINA", "PAGINA", "PÚBLICO", "PUBLICO", "RAMA", "JUDICIAL",
    "JUZGADO", "CIRCUITO", "PENAL", "LABORAL", "CÓDIGO", "CODIGO", "POSTAL",
    "CÉDULA", "CEDULA", "CIUDADANÍA", "CIUDADANIA",
    "FUNDACIÓN", "FUNDACION", "CASA", "HOGAR",
    "INFORME", "POLICIAL", "IDENTIFICACIÓN", "IDENTIFICACION",
    "IDENTIFICACION", "IDENTIFICACIÓN",
    "NUIP", "EPS", "ADRES",  # salud/identificación
    "OK", "KK",               # ruido OCR “Ok Ok …”
    "PARTICULA", "PARTÍCULA",
    "OG", "OCTUBHE",
    "HOSPITAL", "DANE", "COMISARIA", "COMISARÍA",
    "ORGANIZACION", "ORGANIZACIÓN", "DEMANDANTE",
    "EJECUTORIA", "EJECUTORÍA", "PREPARACION", "PREPARACIÓN",
    "NOMBRES", "SEGUNDO", "APELLIDO", "FECHA", "EXPEDICION", "EXPEDICIÓN",
    "LUGAR", "NACIMIENTO", "ACREDITAR", "PARENTESCO",
    "REGISTRO", "DEFUNCION", "DEFUNCIÓN", "MEDICINA", "LEGAL",
    "VIGILANCIA", "FISCAL", "CONTRALORIA", "CONTRALORÍA",
    "DESPACHO", "IDIOMAS", "TDIOMAS",
}

BLACKLIST_PHRASES = {
    "ocr pagina",
    "cedula de ciudadania",
    "codigo postal",
    "informe policial",
    "fundacion casa hogar",
    "identificacion",
}

BLACKLIST_REGEXES = [
    re.compile(r"(?i)\bjuzgado\s+(?:primero|segundo|tercero|cuarto|quinto|sexto|séptimo|septimo|octavo|noveno|d[eé]cimo|\d+|[ivxlcdm]+)\s+(?:penal|laboral)\s+del\s+circuito\b"),
    re.compile(r"(?i)\bjuzgado\s+(?:\w+\s+){0,4}(?:penal|laboral)\s+del\s+circuito\b"),
    re.compile(r"(?i)\bn[uú]mer[o0]\s+de\s+preparaci[oóeé]n\b"),
    re.compile(r"(?i)\bforma(?:to)?\s+dane(?:\s+\w+)?\b"),
    re.compile(r"(?i)\borganizaci[oó]n\s+electoral\b"),
    re.compile(r"(?i)\bnorte\s+de\s+santander\b"),
    re.compile(r"(?i)\bvence\s+ejecutor[ií]a(?:\s+\w+)?\b"),
    re.compile(r"(?i)\bhospital\s+[A-ZÁÉÍÓÚÑ ]{3,}\b"),
    re.compile(r"(?i)\bfecha\s+de\s+expedici[oó]n\b"),
    re.compile(r"(?i)\blugar\s+de\s+nacimient[oa]\b"),
    re.compile(r"(?i)\bacreditar\s+parentesco\b"),
    re.compile(r"(?i)\bregistro\s+de\s+defunci[oó]n\b"),
    re.compile(r"(?i)\bmedicina\s+legal\b"),
    re.compile(r"(?i)\bmedicina\s+legal\s+y\b"),
    re.compile(r"(?i)\bn[uú]mero\s+(?:de\s+)?despacho\b"),
    re.compile(r"(?i)\bdirecci[oó]n\s+de\s+vigilancia\s+fiscal\s+de\s+la\s+contralor[ií]a\b"),
    re.compile(r"(?i)\bbol[ií]var\s+turbaco\b"),
    re.compile(r"(?i)\bvalle\s+del\s+c(?:a[uú]ca|att?ca)\b"),
    re.compile(r"(?i)\bn[uú]mer[o0]\s+de\s+preparac.{0,4}n\b"),
    re.compile(r"(?i)\bnombres\b"),
    re.compile(r"(?i)\bsegundo\s+apellido\b"),
    re.compile(r"(?i)\b[ti]diomas\b"),
    re.compile(r"(?i)\bfecha\b"),
    re.compile(r"(?i)\bseguridad\s+social\b"),
    re.compile(r"(?i)\bcancelada\s+por\s+muerte\b"),
    re.compile(r"(?i)\bresoluci[oó]n\b"),
    re.compile(r"(?i)\b(?:fecha|municipio)[' ]*de\s*preparac.{0,4}n\b"),
    re.compile(r"(?i)\bparte\s+comple\w*\b"),
    re.compile(r"(?i)\bsangu[ií]neo\b"),
    re.compile(r"(?i)\bmoncaleano\s+radicaci[oó]n\b"),
    re.compile(r"(?i)\bfactura\s+electr[oó]nica\s+de\s+venta\b"),
    re.compile(r"(?i)\brepresentaci[oó]n\s+gr[aá]fica(?:\s+(?:de\s+)?datos)?\b"),
    re.compile(r"(?i)\bsector\s+defensa\s+y\s+seguridad\b"),
    re.compile(r"(?i)\bsuperintendencia\s+de\s+notariado(?:\s+y\s+registro)?\b"),
    re.compile(r"(?i)\bmanizales\s+caldas\b"),
    re.compile(r"(?i)\b(?:zona|municipio)[' ]*de\s*(?:preparac|expedici)[oóeé]n\b"),
    re.compile(r"(?i)\bfresno['’]?\s+tol\b"),
    re.compile(r"(?i)\bte\s+wor\s+es\b"),
    re.compile(r"(?i)\bwerte\s+visibles\b"),
    re.compile(r"(?i)\bbellawes\s+notoria\b"),
    re.compile(r'(?i)\bnotar[ií]a\s+(?:[uú]nica|primera|segunda|tercera|cuarta|quinta|sexta|s[eé]ptima|octava|novena|d[eé]cima|[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+)(?:\s+del?\s+(?:c[ií]rculo|distrito|municipio)\s+de\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ ]+)?\b'),
    re.compile(r"(?i)\bseccional\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+\b"),
    re.compile(r"(?i)\bconsejo\s+superior\s+de\s+la\s+judicatura\b"),
    re.compile(r"(?i)\bfiscal[ií]a\s+general\s+de\s+la\s+naci[oó]n\b"),
    re.compile(r"(?i)\bprocuradur[ií]a\s+general\s+de\s+la\s+naci[oó]n\b"),
    re.compile(r"(?i)\bdefensor[ií]a\s+del\s+pueblo\b"),
    re.compile(r"(?i)\binstituto\s+colombiano\s+de\s+bienestar\s+familiar\b"),
    re.compile(r"(?i)\bpacto\s+internacional\s+de\s+derechos\b"),
    re.compile(r"(?i)\bconvenci[oó]n\s+americana\b"),
    re.compile(r"(?i)\bderechos\s+humanos\b"),
    re.compile(r"(?i)\bdecreto\s+ley\b"),
    re.compile(r"(?i)\b(en\s+la\s+)?sentencia\s+[a-z]\b"),
    re.compile(r"(?i)\b(d[eé]cimo\s+(?:primero|segundo|tercero|cuarto)|hechos\s+primero|pretensiones\s+primero)\b"),
    re.compile(r"(?i)\blink\s+para\s+acceder\b"),
    re.compile(r"(?i)\braz[oó]n\s+social\b"),
    re.compile(r"(?i)\bactividad\s+econ[oó]mica\b"),
    re.compile(r"(?i)\bdatos\s+del?\s+(?:emisor|adquirient[eo])\b"),
    re.compile(r"(?i)\bretenciones?\b"),
    re.compile(r"(?i)\brete\s+(?:iva|ica)\b"),
    re.compile(r"(?i)\bmoneda\b"),
    re.compile(r"(?i)\btasa\s+de\s+cambio\b"),
    re.compile(r"(?i)\bn[uú]mero\s+(?:[úu]nico\s+)?de\s+transacci[oó]n\b"),
    re.compile(r"(?i)\bhuella\s+impres[ao]\b"),
    re.compile(r"(?i)\b[ií]ndice\s+(?:derecho|izquierdo)\b"),
    re.compile(r"(?i)\bn[uú]mero\s+de\s+impresi[oó]n\b"),
    re.compile(r"(?i)\bseñales\s+particulares\b"),
    re.compile(r"(?i)\bsanta\s+rosa(?:\s+de\s+lima)?\b"),
    re.compile(r"(?i)\bsantiago\s+de\s+cali\b"),
    re.compile(r"(?i)\bibagu[eé]\s+tolima\b"),
    re.compile(r"(?i)\briohacha\s+y\s+santa\s+marta\b"),
    re.compile(r"(?i)\bdistrito\s+de\s+buenaventura\b"),
    re.compile(r"(?i)\bvereda\s+la\s+fiel\b"),
    re.compile(r"(?i)\bc[ií]rculo\s+de\s+barranquilla\b"),
    re.compile(r"(?i)\bedificio\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+){0,3}\b"),
    re.compile(r"(?i)\b(?:ok|kk)(?:\s+(?:ok|kk)){1,}\b"),
    re.compile(r"(?i)\bnombres?\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+\s+apellidos?\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+\b"),
    re.compile(r"(?i)\beps\s+mutual\s*ser\b"),
    re.compile(r"(?i)\bmutual\s*ser\b"),
    re.compile(r"(?i)\badres\b"),
    re.compile(r'(?i)\bnotar[ií]a\s+(?:[uú]nica|primera|segunda|tercera|cuarta|quinta|sexta|s[eé]ptima|octava|novena|d[eé]cima|[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+)(?:\s+del?\s+(?:c[ií]rculo|distrito|municipio)\s+de\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ ]+)?\b'),
    re.compile(r"(?i)\b[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+){0,2}\s+notar[ií]a\b"),
    re.compile(r"(?i)\bdirecci[oó]n\s+seccional\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+\b"),
    re.compile(r"(?i)\bseccional\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ]+\b"),
    re.compile(r"(?i)\bconsejo\s+superior\s+de\s+la\s+judicatura\b"),
    re.compile(r"(?i)\bfiscal[ií]a\s+general\s+de\s+la\s+naci[oó]n\b"),
    re.compile(r"(?i)\bprocuradur[ií]a\s+general\s+de\s+la\s+naci[oó]n\b"),
    re.compile(r"(?i)\bdefensor[ií]a\s+del\s+pueblo\b"),
    re.compile(r"(?i)\binstituto\s+colombiano\s+de\s+bienestar\s+familiar\b"),
    re.compile(r"(?i)\b(link\s+para\s+acceder|hechos\s+primero|pretensiones\s+primero)\b"),
    re.compile(r"(?i)\bdecreto\s+ley\b"),
    re.compile(r"(?i)\bpacto\s+internacional\s+de\s+derechos\b"),
    re.compile(r"(?i)\bconvenci[oó]n\s+americana\b"),
    re.compile(r"(?i)\bderechos\s+humanos\b"),
    re.compile(r"(?i)\bacceso\s+carnal\b"),
    re.compile(r"(?i)\bacto\s+sexual\s+abusivo\b"),
    re.compile(r"(?i)\bincapacidad\s+de\s+resistir\b"),
    re.compile(r"(?i)\ben\s+averiguaci[oó]n\b"),
    re.compile(r"(?i)\bolaya\s+herrera(?=,|\s+(?:aeropuerto|barrio|comuna|medell[ií]n|tulu[aá]|valle|cali)\b)"),
    re.compile(r"(?i)\btul[uú]a\s+valle\b"),
    re.compile(r"(?i)\bpopay[aá]n\b"),
    re.compile(r"(?i)\bhuella\s+impres[ao]\b"),
    re.compile(r"(?i)\b[ií]ndice\s+(?:derecho|izquierdo)\b"),
    re.compile(r"(?i)\bn[uú]mero\s+de\s+impresi[oó]n\b"),
    re.compile(r"(?i)\bseñales\s+particulares\b"),
    re.compile(r"(?i)\bpublicaci[oó]n\s+por\s+equip\b"),
    re.compile(r"(?i)\bdescuento\s+global\b"),
    re.compile(r"(?i)\brecargo\s+global\b"),
    re.compile(r"(?i)\banticipos?\b"),
    re.compile(r"(?i)\binc\s+bolsas\b"),
    re.compile(r"(?i)\biva\s+inc\s+bolsas\b"),
    re.compile(r"(?i)\bn[uú]mero\s+(?:[úu]nico\s+)?de\s+transacci[oó]n\b"),
    re.compile(r"(?i)\bexistencia\s+uni[oó]n\s+marital\s+de\s+hecho\b"),
    re.compile(r"(?i)\bentre\s+calles\b"),
    re.compile(r"(?i)\bapellidos?\s+y\s+nombres?\b"),
]

_NEW_FP_PHRASES = {
    "DATOS DE IA",
    "OG",
    "OCTUBHE",
    "BACHILLER BEADÉNIEO CON",
    "SEGURIDAD SOCIAL",
    "CANCELADA POR MUERTE",
    "RESOLUCIÓN",
    "SANGUINEO APE",
    "PARTE COMPLE",
    "MONCALEANO RADICACIÓN",
    "MUNICIPIO\'DE PREPARACIÉN",
    "FECHADE PREPARACIÉN",
    "EULA AFELLIOOS",
    "santa rosa", "santa rosa de lima", "rosa de lima",
    "santiago de cali", "ibagué tolima", "riohacha y santa marta",
    "vereda la fiel", "circulo de barranquilla", "distrito de buenaventura",
    "consejo superior de la judicatura", "fiscalía general de la nación",
    "procuraduría general de la nación", "defensoría del pueblo",
    "información ciudadana",
    "correo electrónico", "persona jurídica", "medida provisional", "debido proceso",
    "archivo", "cordialmente", "aviso de confidencialidad", "derechos del niño",
    "constitución política", "contencioso administrativo", "secretaría técnica",
    "dirección de censo electoral", "hechos primero", "pretensiones primero",
    "fundamentos jurídicos", "fundamentos de derecho", "juramento manifiesto",
    "notificaciones", "derecho de petición", "poder especial",
    "administradora de los recursos del sistema general",
    "base de datos única de afiliados", "información básica del afiliado",
    "eps mutual ser", "mutualser",
    "número de factura", "medio de pago", "tipo de operación", "datos del emisor",
    "razón social", "actividad económica", "datos del adquiriente", "total bruto factura",
    "tasa de cambio", "subtotal", "número de autorización", "solución gratuita dian",
    "xml generado", "pdf generado",
    "huella impresa", "índice derecho", "número de impresión",
    "señales particulares", "vigencia", "estatura", "dirección de residencia",
    "teléfono",
    "clase proceso", "tipo reparto",
    "correo electrónico", "persona jurídica", "archivo", "cordialmente",
    "aviso de confidencialidad", "derechos del niño", "constitución política",
    "derecho internacional", "personalidad jurídica", "fundamentos jurídicos",
    "fundamentos de derecho", "juramento manifiesto", "derecho de petición",
    "notificaciones", "poder especial", "expediente constitucional",
    "pruebas sírvase", "procedimiento es", "competencia es",
    "competencia radicación", "por secretaría",
    "brasil y argentina", "europa y asia", "italia y francia",
    "oriente medio", "imperio otomano", "estados unidos",
    "santa rosa de lima", "san onofre", "maría la baja",
    "olimpia it", "publicacion por equip", "descuento global", "recargo global",
    "anticipos", "inc bolsas", "iva inc bolsas", "imprimir cerrar ventana", "pm descargue",
    "copia tomada del original", "constatación de la identidad",
    "notifíquese y cúmplase",
    "existencia union marital de hecho", "entre compañeros permanentes",
}

_NEW_FP_PHRASES_v3 = {
    "FACTURA ELECTRÓNICA DE VENTA",
    "REPRESENTACIÓN GRÁFICA DATOS",
    "FRESNO\' TOL",
    "ES GRATUITA",
    "SECTOR DEFENSA Y SEGURIDAD",
    "SUPERINTENDENCIA DE NOTARIADO",
    "TE WOR ES",
    "MANIZALES CALDAS",
    "ZONADE PREPARACIÉN",
    "MUNICIPIO DE EXPEDICIÉN",
    "BELLAWES NOTORIA",
    "WERTE VISIBLES",
}

NEW_PHRASES = {
    "DATOS DE IA",
    "OG OCTUBHE",
    "FORMA DANE IP",
    "ORGANIZACION ELECTORAL",
    "HOSPITAL SAN JOSÉ DE GUADUAS",
    "NÚMERO DE PREPARACIÓN",
    "ADOPCIÓN DE MAYORES DEMANDANTE",
    "VENCE EJECUTORIA AGOSTO",
    "COMISARIA KS",
    "NORTE DE SANTANDER",
    "NUMERO DE PREPARACIÉN",
    "PRIMER APELLIDO",
    "EULA AFELLIOOS",
}

NEW_PHRASES_2 = {
    "AGED NAE PICOTA",
    "VALLE DEL CATTCA EB",
    "BOLIVAR TURBACO",
    "FECHA DE EXPEDICIÓN",
    "DIRECCIÓN DE VIGILANCIA FISCAL DE LA CONTRALORÍA",
    "NOMBRES",
    "LUGAR DE NACIMIENTO",
    "ACREDITAR PARENTESCO",
    "REGISTRO DE DEFUNCION",
    "MEDICINA LEGAL Y",
    "TURBACO",
    "NÚMERO DESPACHO",
    "ANDRADE ADOPTIVAS",
    "SEGUNDO APELLIDO",
    "TDIOMAS",
    "FECHA",
    "NUMERO DE PREPARACLÉN",
}

# Actualizar sets con las nuevas frases
BLACKLIST_PHRASES.update({_norm_phrase(p) for p in _NEW_FP_PHRASES})
BLACKLIST_PHRASES.update({_norm_phrase(p) for p in _NEW_FP_PHRASES_v3})
BLACKLIST_PHRASES.update({_norm_phrase(p) for p in NEW_PHRASES})
BLACKLIST_PHRASES.update({_norm_phrase(p) for p in NEW_PHRASES_2})

# ===================== Tokens base para nombres =====================

NAME_WORD_UPPER = r"[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ'`´-]+"
NAME_WORD_TITLE = r"[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü'`´-]+"
NAME_TOKEN      = rf"(?-i:(?:{NAME_WORD_TITLE}|{NAME_WORD_UPPER}))"
CONNECTOR_RE    = r"(?-i:(?:d[ea]l?|y|la|las|los|da|do|das|dos))"
SENOR_VARIANTS  = r"(?:se(?:ñ|n|f(?:i|fi))?or(?:a)?|sr\.?|sra\.?)"

# ===================== Campos tipo “Primer/Segundo …” =====================

RE_FIELD_LINE   = re.compile(r"(?im)^[ \t]*[*•-]?\s*(Primer|Segundo)\s+(Apellido|Nombre)\s*:\s*(.*)$")
NAME_TOKEN_CHARS= r"[A-Za-zÁÉÍÓÚÑÜáéíóúüñ'`´-]{2,}"
RE_NAME_TOKENS  = re.compile(NAME_TOKEN_CHARS)

# ===================== Patrones de frases =====================

RE_CONTRA = re.compile(
    rf"\bcontra\s+(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})\s*(?=[,.;:)\]]|\s|$)",
    re.IGNORECASE | re.DOTALL
)

RE_A_NOMBRE = re.compile(
    rf"(?:a\s+nombre\s+del?\s+{SENOR_VARIANTS}|del?\s+{SENOR_VARIANTS}|como\s+del?\s+{SENOR_VARIANTS}|tanto\s+del?\s+{SENOR_VARIANTS})\s+"
    rf"(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})\s*(?=[,.;:)\]]|\s|$)",
    re.IGNORECASE | re.DOTALL
)

RE_SENOR = re.compile(
    rf"\b{SENOR_VARIANTS}\s+(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})\s*(?=[,.;:)\]]|\s|$)",
    re.IGNORECASE | re.DOTALL
)

RE_SLP = re.compile(
    rf"correspondiente\s+al\s+SLP\.?\s+(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})",
    re.IGNORECASE | re.DOTALL
)

RE_SIG_PERSONAS = re.compile(
    rf'de\s+las\s+siguientes\s+personas\s*:\s*["“”«»]?\s*(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})',
    re.IGNORECASE | re.DOTALL
)

RE_NOMBRE_DEL_SENOR = re.compile(
    rf"\bnombre\s+del?\s+{SENOR_VARIANTS}\s+"
    rf"(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})\s*(?=[,.;:)\]]|\s|$)",
    re.IGNORECASE | re.DOTALL
)

RE_ACCIONANTE = re.compile(
    rf"\baccionante\s*:\s*(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})\s*(?=,|\.|\n|$|\s+identificad[oa]\b|\s+c\.?c\.?\b|\s+cc\b)",
    re.IGNORECASE | re.DOTALL
)

RE_TUTELA_PROMOVIDA = re.compile(
    r"(?:acci[oó]n\s+de\s+)?tutela\s+promovida\s+por\s+"
    rf"(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})"
    r"\s*(?=,|\.|\n|$|\s+identificad[oa]\b|\s+c\.?c\.?\b|\s+cc\b)",
    re.IGNORECASE | re.DOTALL
)

RE_CONTRA_HEREDEROS = re.compile(
    r"\bcontra\s+(?:los\s+)?herederos"
    r"(?:\s+determinados?)?"
    r"(?:\s+(?:e|y)\s+indeterminados?)?"
    r"\s+de\s+"
    rf"(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{0,6}})",
    re.IGNORECASE | re.DOTALL
)

RE_MAYOR_IDENT = re.compile(
    rf"(?P<name>{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{1,6}})"
    r"\s*,\s*mayor\s+de\s+edad\b.*?"
    r"(?=,|\.|\n|$|\s+identificad[oa]\b|\s+c\.?c\.?\b|\s+c[eé]dula\b)",
    re.IGNORECASE | re.DOTALL
)

# ===================== Pre-contextos a omitir =====================

PRE_CONTEXT_BLOCK = re.compile(
    r"(?i)(apoderad[oa]\s+de|en\s+calidad\s+de\s+apoderad[oa]\s+de|poderdante|"
    r"edificio|vereda|parroquia|corregimiento|municipio|barrio|comuna|rancher(?:i|í)a)\s*$"
)

PRE_CONTEXT_AUTH = re.compile(
    r"(?i)(?:por\s+el\s+se(?:ñ|n)or\s+)?(?:magistrad[oa]|juez|jueza|relator(?:a)?|secretari[oa]|escribiente)\s*$"
)

# ===================== Bloques tras números grandes =====================

RE_NUM_LINE   = re.compile(r"^\s*\d[\d.,]{5,}[\s\-–]*$", re.MULTILINE)
RE_UPPER_TOKEN= re.compile(r"^[A-ZÁÉÍÓÚÑÜ'`´-]{2,}$")

# ===================== Barredor genérico =====================

RE_GENERIC = re.compile(
    rf"\b{NAME_TOKEN}(?:\s+(?:{CONNECTOR_RE}|{NAME_TOKEN})){{1,6}}\b"
)

# ===================== Cedulas =====================

CEDULA_NUM_ANY = re.compile(r"(?:\d{1,3}(?:[.,\-\s]\d{3})+|(?<!\d)\d{6,10}(?!\d))")
CEDULA_VERIF_PAT = r"c[oó]digo|verificaci[oó]n|verificar|autenticidad|consulte|ingres[ea]\s+el\s+c[oó]digo"
CEDULA_BLACKLIST_FIELDS = (
    r"impresi[oó]n|fabricaci[oó]n|huella|ind(?:ice|i[cs]e)|validez|estado\s+de\s+la\s+versi[oó]n|"
    r"documento\s+base|tipo\s+del\s+documento\s+base|n[uú]mero\s+del\s+documento\s+base|"
    r"notaria|tel[eé]fono|grupo\s+sangu[ií]neo|factor\s+rh|se[nñ]ales\s+particulares|"
    r"direcci[oó]n|residencia|ciudad\s+de\s+residencia|p[aá]gina|pagina"
)
CEDULA_PRIMARY_TOKENS = r"\b(cedula|nuip|nip|cc|n[uú]mero\s+de\s+documento)\b"
CEDULA_NO_FUZZ = r"(?:n[ou]mero|no\.?|n[°ºo])"
CEDULA_RAD_LABEL = re.compile(
    r"(?:radicaci[óo]n|radicad[oa]|rad\.)\s*"
    r"(?:n(?:o\.?|[°º])|num(?:ero)?)?\s*[:\-]?\s*[\r\n\s]*"
    r"((?:\d{1,6}(?:[.\-\s]\d{1,6}){2,}))",
    flags=re.DOTALL
)

# ===================== Resumen =====================

SUMMARY_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
SUMMARY_WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", re.UNICODE)

# ===================== Constantes de Comprehend =====================

LANG = "es"
THRESHOLD = 0.85
CHUNK_SIZE = 4500
SOFT_SPLIT = r"(?<=[\.\n])\s+"

# Frases de contexto que invalidan un candidato cercano
FRASES_PROHIBIDAS = [
    # originales
    "por el señor magistrado","por la señora magistrada",
    "por el señor juez","por la señora jueza",
    "por el magistrado","por la magistrada","por el juez","por la jueza",
    # nuevas por falsos positivos
    "factura electrónica de venta","factura electronica de venta","dane","ibague","ibagué",
    "segundo nombre","primer nombre","particula","partícula","sexo","masculino","femenino",
    "los meses","ip",
    # procesos/plantillas
    "acción de tutela", "remite por competencia", "por secretaría", "informe secretarial",
    "constancia secretarial", "traslado de tutela", "tipo de demanda", "código del juzgado",
    "acta individual de reparto", "número radicación", "fecha presentación", "clase proceso",
    "tipo reparto", "presunción de muerte", "cancelada por muerte",
    # biométricos / consulta web
    "consulta web", "vista detallada", "grupo sanguíneo", "señales particulares",
    "documento base", "huella impresa", "pulgar", "índice", "anular", "meñique",
    # recaudos/facturas
    "recibo de pago", "transacción exitosa", "solución gratuita",
    # institucional
    "consejo superior de la judicatura", "defensoría del pueblo", "personería municipal",
    "superintendencia de notariado",
    # varias del dataset
    "edificio córdoba", "edificio comando", "brigada de selva",
    "delegación departamental", "rectificación de cédula",
]

# Palabras que si aparecen como PRIMER token, descartamos (encabezados, secciones)
HEADERS_BLACKLIST = {
    "REPUBLICA","REPÚBLICA","JUZGADO","OFICIO","SEÑORES","DISTRITO","MUNICIPAL",
    "REGISTRADURIA","REGISTRADURÍA","ESTADO","CIVIL","HECHOS","PRETENSIONES",
    "PRUEBAS","ANEXOS","NOTIFICACIONES","COMPETENCIA","PROCEDIMIENTO",
    "FUNDAMENTOS","DERECHO","ARTICULO","ARTÍCULOS",
    # refuerzos anti-registro/certificaciones/plantillas
    "FONDO","ROTATORIO","FIEL","COPIA","ORIGINAL","REGISTRO","NACIMIENTO",
    "DEFUNCION","DEFUNCIÓN","CERTIFICA","CERTIFICACION","CERTIFICACIÓN"
}

HEADERS_BLACKLIST |= {
    # institucional/órganos
    "CONSEJO","CORTE","SALA","FISCALIA","FISCALÍA","PROCURADURIA","PROCURADURÍA",
    "PERSONERIA","PERSONERÍA","REGISTRADURIA","REGISTRADURÍA","HOSPITAL","EPS",
    "NOTARIA","NOTARÍA","SECCIONAL","BRIGADA","UNIDAD","ADMINISTRATIVA","ESPECIAL",
    # plantillas/biométricos
    "CONSULTA","VISTA","GRUPO","SEÑALES","HUELLA","PULGAR","INDICE","ÍNDICE",
    "ANULAR","MEÑIQUE","ACTA","CLASE","TIPO","FECHA","NÚMERO","NUMERO","CÓDIGO","CODIGO",
    # actos/trámites
    "DEMANDA","PODER","ACCION","ACCIÓN","RESOLUCION","RESOLUCIÓN","CERTIFICADO",
    "CERTIFICACION","CERTIFICACIÓN","REPARTO","RADICACION","RADICACIÓN",
    # títulos comunes que llegan en OCR
    "SEÑOR","SEÑORA","SR.","SRA.",
}

# Stopwords / ruido que INVALIDAN si aparecen en CUALQUIER token del candidato
DEMONYM_STOPWORDS = {
    # (los que ya tenías)
    "italiano","italianos","italiana","italianas",
    "español","españoles","española","españolas",
    "francés","franceses","francesa","francesas",
    "venezolano","venezolanos","venezolana","venezolanas",
    "brasileño","brasileños","brasileña","brasileñas",
    "argentino","argentinos","argentina","argentinas",
    "colombiano","colombianos","colombiana","colombianas",
    "asiático","asiáticos","asiática","asiáticas",
    "europeo","europeos","europea","europeas",
    "judicial","civil","penal","público","pública",
    "archivo","nacional","identificación",
    # (los que añadimos antes por falsos positivos)
    "sexo","factura","electrónica","electronica","venta","ibague","ibagué","meses",
    "particula","partícula","masculino","femenino","dane","ip","octubhe","og","pqiv","ge","meh","ctms",
    # nuevos por tus casos
    "fondo","rotatorio","fiel","copia","original",
    "registro","nacimiento","defunción","defuncion"
}

PHRASES_BLACKLIST = {
    "fondo rotatorio de la registraduría",
    "fondo rotatorio de la registraduria",
    "fiel copia tomada del original",
    "registro de nacimiento",
    "registro de defunción",
    "registro de defuncion",
    "de registro nacimiento",
}

# Partículas válidas en nombres hispanos que pueden ser cortas
ALLOWED_PARTICLES = {"de","del","la","las","los","y","san","santa","da","do","das","dos"}

UPPER_PAT = re.compile(r"\b([A-ZÁÉÍÓÚÑÜ]{2,}(?:[ \t]+[A-ZÁÉÍÓÚÑÜ]{2,}){1,6})\b")
TITLE_PAT = re.compile(r"\b([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+(?:[ \t]+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+){1,6})\b")
