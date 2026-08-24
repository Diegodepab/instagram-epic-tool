# Laboratorio aislado

Este directorio contiene copias vendorizadas de proyectos de terceros para evaluación controlada. No implica respaldo de sus funciones ni autorización para usarlas contra cuentas ajenas.

## Límites

- `instagrapi/`: el backend instala esta copia, pero su conector permanece desactivado salvo que el operador defina `ENABLE_INSTAGRAPI_LAB=true`. Solo se admite una cuenta propia o expresamente autorizada.
- `Instagram-/`: contiene código de fuerza bruta. CircleScope no lo importa ni lo ejecuta. La única integración permitida calcula un informe estático mediante AST y hashes, sin darle red.

No añadas credenciales, sesiones, cookies, diccionarios, proxies ni exportaciones reales a este directorio. Conserva las licencias originales y revisa [el aviso general](../DISCLAIMER.md) y [la evaluación de riesgos](../docs/LAB_RISK_ASSESSMENT.md).
