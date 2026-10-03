# PDF → Excel Invoice Automation

English: [README.md](README.md)

![CI](https://github.com/gabrielvalle-491/pdf-invoice-to-excel/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Automatiza la extracción de facturas y documentos a archivos de Excel estructurados y listos para el análisis.

Se coloca una carpeta con facturas de proveedores (PDF) y se obtiene un único libro de Excel con cada
factura, cada línea de detalle, totales automáticos por moneda y una hoja **Review**
que lista todo lo que no cierra, sin carga manual de datos.

## El problema de negocio

Un equipo de cuentas a pagar recibe decenas de facturas de proveedores por semana, de
distintos proveedores, en **distintos idiomas, formatos de fecha y formatos numéricos**
(`1.234,56` vs `1,234.56`, `15/03/2026` vs `Mar 15, 2026`). Alguien carga cada una a mano
en una planilla: un trabajo lento, tedioso y propenso a errores.

## Qué hace esta herramienta

| Paso | Detalle |
|------|---------|
| 1. Leer | Abre cada PDF de una carpeta (texto + tablas) con `pdfplumber` |
| 2. Extraer | Proveedor, identificación fiscal, número de factura, fechas, moneda, subtotal, impuesto, total y cada línea de detalle. Funciona con etiquetas en inglés **y** en español |
| 3. Normalizar | Detecta automáticamente la coma o el punto decimal y 6 formatos de fecha |
| 4. Validar | Líneas de detalle = subtotal, subtotal + impuesto = total, cantidad × precio = importe, vencimiento posterior a la fecha de emisión, campos obligatorios presentes |
| 5. Exportar | Libro de Excel con formato: **Summary**, **Invoices**, **Line Items**, **Review** (con fórmulas de Excel activas, filtros, encabezados inmovilizados y formato de moneda) |

Las facturas que no superan algún control se resaltan y se listan en la hoja **Review** con
el motivo exacto, de modo que una persona solo revisa las excepciones.

## Inicio rápido

```bash
pip install -r requirements.txt

# 1) create 8 realistic sample invoices (EN/ES, ARS/USD)
python -m invoice_extractor.generate_samples samples

# 2) extract them into Excel
python -m invoice_extractor samples -o output/invoices.xlsx
```

```
Processed 8 invoices -> output/invoices.xlsx
  OK: 8 | Needs review: 0
```

## Resultado

**Hoja Invoices** (una fila por factura; los encabezados son los nombres reales de las columnas del Excel):

| File | Vendor | Invoice # | Date | Currency | Subtotal | Tax | Total | Status |
|------|--------|-----------|------|----------|---------:|----:|------:|--------|
| A-01000.pdf | Andes Office Supplies S.A. | A-01000 | 2026-03-28 | ARS | 1,016,000.00 | 213,360.00 | 1,229,360.00 | OK |
| INV-01007.pdf | BlueRiver Cloud Services LLC | INV-01007 | 2026-06-03 | USD | 109.99 | 0.00 | 109.99 | OK |

**Hoja Review** (solo excepciones; ejemplo ilustrativo):

| File | Invoice # | Issue |
|------|-----------|-------|
| broken.pdf | – | Could not read PDF |
| INV-0042.pdf | INV-0042 | Subtotal + tax does not match total |

## Estructura del proyecto

```
invoice_extractor/
├── parsing.py           # amount + date normalization (multi-locale)
├── extractor.py         # PDF -> Invoice dataclass + business validation
├── excel_writer.py      # formatted workbook with formulas
├── generate_samples.py  # realistic demo invoices (reportlab)
└── cli.py               # command line interface
tests/                   # pytest suite (runs on every push via GitHub Actions)
```

## Pruebas

```bash
pytest -q
```

La batería de pruebas genera facturas, las extrae y compara cada campo con
los valores de referencia, además de casos límite (PDF dañados, totales incorrectos, formatos numéricos).

## Cómo adaptarlo a un proveedor nuevo

Las etiquetas de los campos están en `FIELD_PATTERNS` (`extractor.py`). Para admitir un formato nuevo
suele bastar con agregar una alternativa a la expresión regular, por ejemplo `Nro\. Comprobante` en el
patrón del número de factura.

## Cómo se lo entregaría a un cliente

Si me contrata para esto, yo:

- Pediría algunas facturas reales de cada uno de sus proveedores (PDF con texto seleccionable) y ajustaría las etiquetas de `FIELD_PATTERNS` hasta que todas se extraigan correctamente.
- Configuraría una única carpeta de entrada compartida: cada semana el equipo deja allí los PDF nuevos y el resto de su rutina no cambia.
- Lo ejecutaría con un solo comando (`python -m invoice_extractor <folder> -o <workbook>.xlsx`), programado semanalmente con el Programador de tareas de Windows o cron, para que el libro esté listo sin que nadie tenga que iniciarlo.
- Entregaría el libro de Excel como resultado: la hoja **Summary** muestra cuántas facturas se procesaron y cuántas requieren revisión, con los totales por moneda.
- Informaría los problemas con los mecanismos propios de la herramienta: cada factura que no supera un control se resalta en **Invoices** y se lista en la hoja **Review** con el motivo exacto (PDF ilegible, campo faltante, totales que no cierran, vencimiento anterior a la fecha de emisión).
- Haría que la ejecución programada sea fácil de supervisar: la consola muestra `OK: n | Needs review: n`, y si la carpeta de entrada no existe o está vacía se muestra un error y el proceso termina con código 1, de modo que el programador de tareas pueda marcar la ejecución fallida.
- Redactaría una guía breve para el equipo y agregaría casos de prueba para cada formato de proveedor nuevo, para que los cambios futuros no afecten a los proveedores existentes.

## Notas

- Todas las facturas de ejemplo son sintéticas, generadas por `generate_samples.py`. No contienen datos reales de clientes.
- Desarrollado con Python y [Claude Code](https://claude.com/claude-code) como asistente de programación con IA.

## Autor

**Gabriel Valle** — Automatización de datos e IA (Excel, PDF, flujos de trabajo) · Villa Mercedes, Argentina · Remoto
