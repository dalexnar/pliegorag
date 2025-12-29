-- Agregar columna checklist_documentos a la tabla pliegos
ALTER TABLE pliegos ADD COLUMN checklist_documentos JSON AFTER datos_extraidos;
