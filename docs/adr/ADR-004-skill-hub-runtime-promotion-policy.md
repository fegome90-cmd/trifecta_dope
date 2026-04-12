# ADR: Proposed Canonical Promotion Policy for `skill-hub` Runtime

## Status
ACCEPTED

> Esta ADR documenta la policy canónica ratificada para SH-003. Con estado `ACCEPTED`, habilita el cierre documental estrictamente limitado a gobernanza, promoción y verificación de la cadena runtime directa auditada.

## Context
El estado actual verificado muestra drift entre `scripts/skill-hub` y `~/.local/bin/skill-hub`, y no aporta evidencia local verificable de una ruta oficial de promoción. Además, el runtime auditado del wrapper puede depender de archivos adicionales fuera del repo. SH-003 requiere una policy única para gobernar ownership, promoción y verificación de cierre sin asumir que el estado objetivo ya existe.

## Decision
Se propone que esta ADR sea la autoridad conceptual de SH-003 una vez ratificada. Se propone una sola fuente versionada para el wrapper y una sola ruta oficial de promoción hacia el runtime instalado. El receipt de promoción se define como evidencia de una promoción ejecutada, no como fuente de verdad autónoma.

## Governed Scope
Quedan dentro de SH-003:
1. `scripts/skill-hub` como origen versionado propuesto;
2. `~/.local/bin/skill-hub` como destino runtime auditado;
3. todo archivo invocado directamente por el wrapper en el runtime auditado al momento del cierre.

Queda fuera cualquier componente no invocado directamente por el wrapper o cualquier deuda funcional separada que deba rastrearse en otros findings.

## Promotion Contract
La promoción propuesta deberá:
- materializar únicamente archivos dentro del alcance gobernado;
- registrar revisión origen, archivos promovidos, rutas destino y hashes esperados;
- dejar un promotion receipt persistido y verificable.

El promotion receipt prueba una promoción concreta; no reemplaza esta ADR ni redefine la policy.

## Verification Contract
El cierre de SH-003 será inválido si:
- falta receipt;
- los archivos instalados no coinciden con el receipt;
- existe una dependencia runtime auditada directamente invocada fuera del alcance gobernado;
- hubo edición manual no trazada sobre la instalación runtime vigente.

## Closure Conditions
SH-003 sólo podrá cerrarse canónicamente cuando se cumplan ambas condiciones:
1. esta ADR haya sido ratificada y su `Status` sea `ACCEPTED`;
2. la instalación vigente esté respaldada por receipt válido y el wrapper junto con toda dependencia runtime auditada directamente invocada queden gobernados por esa misma policy.

Este cierre canónico certifica únicamente la gobernanza, la promoción y la verificación de la cadena runtime directa auditada (`skill-hub` y `skill-hub-cards`); no certifica corrección funcional total de la superficie `skill-hub` ni cierra findings fuera de alcance como SH-006 o SH-008.
