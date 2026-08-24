# Evaluación de riesgos de `lab/`

Los repositorios bajo `lab/` son material de evaluación y no forman parte del runtime de CircleScope. El backend y el frontend no los importan, ejecutan ni empaquetan.

## Política

- Permitido: análisis estático, documentación, detección defensiva y pruebas con datos sintéticos sin red.
- Experimental: automatización sobre una cuenta propia o expresamente autorizada, aislada, con cuotas, auditoría y parada de emergencia.
- Prohibido: fuerza bruta, acceso no autorizado, evasión de controles, acoso y recopilación masiva de datos de terceros.

## `subzeroid/instagrapi`

Cliente no oficial amplio y aparentemente funcional. La copia revisada contiene autenticación y sesiones, consultas de usuarios y medios, historias, mensajería, comentarios, insights y publicación de contenido. Al depender de interfaces privadas, su estabilidad y compatibilidad no están garantizadas y el uso puede activar controles de la plataforma.

No se integra en producción. Una prueba futura deberá preferir primero las APIs oficiales, usar exclusivamente una cuenta de laboratorio autorizada, almacenar secretos fuera del repositorio y aplicar mínimos privilegios y límites estrictos.

La integración experimental se activa únicamente con `ENABLE_INSTAGRAPI_LAB=true`. Acepta una cuenta propia/autorizada, verifica que la identidad autenticada coincida, limita cada muestra a 50 relaciones y 12 medios, aplica un minuto de enfriamiento por cliente y destruye la sesión al terminar sin escribirla a disco.

## `Bitwise-01/Instagram-`

No es una herramienta OSINT. El código acepta un usuario, un diccionario de contraseñas y proxies; paraleliza intentos de autenticación y guarda la credencial cuando detecta una sesión válida. También puntúa y rota proxies.

Clasificación: capacidad ofensiva prohibida. Se conserva únicamente para análisis estático defensivo y nunca debe recibir red, credenciales, diccionarios ni un punto de ejecución desde la aplicación.

Su integración expone exclusivamente un informe generado con el parser AST de Python, hashes SHA-256 y conteos de indicadores. Los módulos del repositorio no se importan ni se ejecutan.

## Controles antes de promover un experimento

1. Propietario y finalidad documentados.
2. Consentimiento y alcance verificables.
3. Threat model y revisión de privacidad.
4. Sandbox sin red por defecto; secretos externos y rotables.
5. Rate limits, logs sin datos sensibles y kill switch.
6. Pruebas automatizadas que aseguren que capacidades prohibidas no son accesibles.
