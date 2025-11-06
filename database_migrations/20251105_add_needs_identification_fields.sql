-- Migration: Add 8 new fields to NEEDS IDENTIFICATION stage
-- Date: 2025-11-05
-- Description: Adding detailed needs identification fields to checklist_analysis table

-- Add 8 new fields for needs identification stage
ALTER TABLE checklist_analysis 
ADD COLUMN need_company_activity DECIMAL(3,1) DEFAULT 0,
ADD COLUMN need_employee_count DECIMAL(3,1) DEFAULT 0,
ADD COLUMN need_sales_department DECIMAL(3,1) DEFAULT 0,
ADD COLUMN need_it_responsible DECIMAL(3,1) DEFAULT 0,
ADD COLUMN need_services_to_connect DECIMAL(3,1) DEFAULT 0,
ADD COLUMN need_additional_offices DECIMAL(3,1) DEFAULT 0,
ADD COLUMN need_equipment_required DECIMAL(3,1) DEFAULT 0,
ADD COLUMN need_workplace_wiring DECIMAL(3,1) DEFAULT 0;

-- Add comments to describe the new fields
COMMENT ON COLUMN checklist_analysis.need_company_activity IS 'Выяснил чем занимается компания, какая сфера деятельности';
COMMENT ON COLUMN checklist_analysis.need_employee_count IS 'Какое количество сотрудников будет пользоваться услугами связи';
COMMENT ON COLUMN checklist_analysis.need_sales_department IS 'Есть ли отдел продаж в компании';
COMMENT ON COLUMN checklist_analysis.need_it_responsible IS 'Кто отвечает за IT инфраструктуру в компании';
COMMENT ON COLUMN checklist_analysis.need_services_to_connect IS 'Какие сервисы планируете подключать к интернету - почта, видеонаблюдение, телефония';
COMMENT ON COLUMN checklist_analysis.need_additional_offices IS 'Есть ли в компании дополнительные офисы в Москве или в других городах';
COMMENT ON COLUMN checklist_analysis.need_equipment_required IS 'Оборудование потребуется или нет';
COMMENT ON COLUMN checklist_analysis.need_workplace_wiring IS 'Требуется ли разводка для рабочих мест';

-- Add check constraints to ensure values are within valid range (0.0 to 10.0)
ALTER TABLE checklist_analysis 
ADD CONSTRAINT check_need_company_activity CHECK (need_company_activity >= 0 AND need_company_activity <= 10),
ADD CONSTRAINT check_need_employee_count CHECK (need_employee_count >= 0 AND need_employee_count <= 10),
ADD CONSTRAINT check_need_sales_department CHECK (need_sales_department >= 0 AND need_sales_department <= 10),
ADD CONSTRAINT check_need_it_responsible CHECK (need_it_responsible >= 0 AND need_it_responsible <= 10),
ADD CONSTRAINT check_need_services_to_connect CHECK (need_services_to_connect >= 0 AND need_services_to_connect <= 10),
ADD CONSTRAINT check_need_additional_offices CHECK (need_additional_offices >= 0 AND need_additional_offices <= 10),
ADD CONSTRAINT check_need_equipment_required CHECK (need_equipment_required >= 0 AND need_equipment_required <= 10),
ADD CONSTRAINT check_need_workplace_wiring CHECK (need_workplace_wiring >= 0 AND need_workplace_wiring <= 10);