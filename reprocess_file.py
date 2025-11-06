#!/usr/bin/env python3
"""
Script to reprocess a file with the new analysis system
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from database_service import DatabaseService
from openai_service import OpenAIService
from sqlalchemy import create_engine, text

async def reprocess_file(file_id: str):
    """Reprocess a file with new analysis system."""
    load_dotenv()
    
    print(f'Reprocessing file {file_id} with new analysis system...')
    
    # Initialize services
    db_service = DatabaseService()
    openai_service = OpenAIService()
    
    # Get call record
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, transcription_text, tagged_dialogue, file_name
            FROM call_records 
            WHERE file_id = :file_id
        """), {'file_id': file_id})
        record = result.fetchone()
        
        if not record:
            print('❌ Call record not found')
            return
            
        call_record_id, transcription, tagged_dialogue, file_name = record
        print(f'Processing: {file_name}')
        
        # Perform AI analysis
        try:
            # Use structured analysis instead of quality score
            ai_result = await openai_service.structured_call_analysis(transcription)
            print(f'✅ AI analysis completed - Contact: {ai_result.contact_establishment.value}, Needs: {ai_result.needs_identification.value}')
            
            # Perform checklist analysis  
            checklist_result = await openai_service.checklist_analysis(tagged_dialogue)
            print(f'✅ Checklist analysis completed')
            
            # Print some results to verify
            need_stage = checklist_result.stage_need_identification
            print(f'Need identification stage results:')
            for key, value in need_stage.items():
                print(f'  - {key}: {value}')
            
            # Save AI analysis
            session = db_service.get_session()
            try:
                from database_models import AIAnalysis, ChecklistAnalysis
                
                # Create AI analysis record
                ai_analysis = AIAnalysis(
                    call_record_id=call_record_id,
                    summary=ai_result.summary,
                    client_talks_most=ai_result.client_talks_most,
                    client_name=ai_result.client_name,
                    style_adaptation=ai_result.style_adaptation,
                    target_client=ai_result.target_client,
                    client_needs=ai_result.client_needs,
                    manager_responsible=ai_result.manager_responsible,
                    contact_establishment_value=ai_result.contact_establishment.value,
                    contact_establishment_explanation=ai_result.contact_establishment.explanation,
                    qualification_value=ai_result.qualification.value,
                    qualification_explanation=ai_result.qualification.explanation,
                    needs_identification_value=ai_result.needs_identification.value,
                    needs_identification_explanation=ai_result.needs_identification.explanation,
                    product_presentation_value=ai_result.product_presentation.value,
                    product_presentation_explanation=ai_result.product_presentation.explanation,
                    objection_handling_value=ai_result.objection_handling.value,
                    objection_handling_explanation=ai_result.objection_handling.explanation,
                    closing_value=ai_result.closing.value,
                    closing_explanation=ai_result.closing.explanation,
                    sale_probability_value=ai_result.sale_probability.value,
                    sale_probability_explanation=ai_result.sale_probability.explanation,
                    hidden_objections=ai_result.hidden_objections,
                    next_step=ai_result.next_step
                )
                session.add(ai_analysis)
                
                # Map checklist fields properly
                field_mapping = {
                    # Need identification NEW fields
                    "Finds out employee count for services": "need_employee_count",
                    "Checks if company has sales department": "need_sales_department", 
                    "Identifies IT infrastructure responsible person": "need_it_responsible",
                    "Clarifies services to connect to internet": "need_services_to_connect",
                    "Asks about additional offices in Moscow or other cities": "need_additional_offices",
                    "Determines if equipment is required": "need_equipment_required",
                    "Checks if workplace wiring is needed": "need_workplace_wiring",
                }
                
                # Update existing checklist analysis with new NEEDS fields
                existing_checklist = session.query(ChecklistAnalysis).filter(
                    ChecklistAnalysis.call_record_id == call_record_id
                ).first()
                
                if existing_checklist:
                    # Update existing record with new NEEDS fields
                    existing_checklist.need_company_activity = need_stage.get('Finds out company activity and business area', 0)
                    existing_checklist.need_employee_count = need_stage.get('Finds out employee count for services', 0)
                    existing_checklist.need_sales_department = need_stage.get('Checks if company has sales department', 0)
                    existing_checklist.need_it_responsible = need_stage.get('Identifies IT infrastructure responsible person', 0)
                    existing_checklist.need_services_to_connect = need_stage.get('Clarifies services to connect to internet', 0)
                    existing_checklist.need_additional_offices = need_stage.get('Asks about additional offices in Moscow or other cities', 0)
                    existing_checklist.need_equipment_required = need_stage.get('Determines if equipment is required', 0)
                    existing_checklist.need_workplace_wiring = need_stage.get('Checks if workplace wiring is needed', 0)
                    
                    print('✅ Updated existing checklist analysis with new NEEDS fields')
                else:
                    print('❌ No existing checklist analysis found to update')
                
                session.commit()
                print('✅ Analysis data saved to database')
                
                # Verify the data was saved
                session.refresh(ai_analysis)
                if existing_checklist:
                    session.refresh(existing_checklist)
                
                print(f'✅ AI Analysis ID: {ai_analysis.id}')
                if existing_checklist:
                    print(f'✅ Checklist Analysis ID: {existing_checklist.id}')
                    print(f'✅ New need_employee_count: {existing_checklist.need_employee_count}')
                    print(f'✅ New need_company_activity: {existing_checklist.need_company_activity}')
                
            except Exception as e:
                session.rollback()
                print(f'❌ Error saving to database: {e}')
                import traceback
                traceback.print_exc()
            finally:
                session.close()
                
        except Exception as e:
            print(f'❌ Error during analysis: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    file_id = "1voqzO7UvnwxJBna1Aib8Npear8YotbOO"  # Овчинников.mp3
    asyncio.run(reprocess_file(file_id))