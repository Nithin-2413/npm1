import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from celery_config import celery_app
from sqlalchemy.orm import Session
import os

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="execute_test_run")
def execute_test_run(self, run_id: str, flow_id: Optional[str], 
                    variables: Dict[str, Any], 
                    natural_language_input: Optional[str],
                    test_env_id: Optional[str]):
    """
    Celery task to execute a test run in the background
    """
    # Run async execution in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _execute_test_run_async(
                run_id=run_id,
                flow_id=flow_id,
                variables=variables,
                natural_language_input=natural_language_input,
                test_env_id=test_env_id
            )
        )
        return result
    except Exception as e:
        logger.error(f"Test run {run_id} failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        loop.close()


async def _execute_test_run_async(run_id: str, flow_id: Optional[str],
                                  variables: Dict[str, Any],
                                  natural_language_input: Optional[str],
                                  test_env_id: Optional[str]) -> Dict[str, Any]:
    """
    Async execution of test run
    """
    from models import SessionLocal, TestRun, StepLog, RCAReport, TestEnvironment
    from core.playwright_engine import PlaywrightEngine
    from core.context_store import ContextStore
    from core.flow_registry import flow_registry
    from core.llm_service import llm_service
    
    db = SessionLocal()
    context = ContextStore(run_id)
    playwright_engine = None
    
    try:
        # Update status to running
        test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
        test_run.status = "running"
        db.commit()
        
        # Get test environment credentials if provided
        test_env = None
        if test_env_id:
            test_env = db.query(TestEnvironment).filter(TestEnvironment.id == test_env_id).first()
            if test_env:
                # Add credentials to variables
                variables['url'] = test_env.url
                variables['username'] = test_env.username
                variables['password'] = test_env.password
        
        # Get flow template
        if not flow_id:
            # TODO: Use LLM to parse natural language and determine flow
            raise ValueError("Natural language flow selection not yet implemented")
        
        flow = flow_registry.get_flow(flow_id)
        if not flow:
            raise ValueError(f"Flow '{flow_id}' not found")
        
        # Initialize Playwright
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        playwright_engine = PlaywrightEngine(run_id=run_id, headless=headless)
        await playwright_engine.initialize()
        
        # Store context
        context.set("flow_id", flow_id)
        context.set("variables", variables)
        
        # Execute each step
        total_steps = len(flow['steps'])
        for idx, step in enumerate(flow['steps'], 1):
            # Check for cancellation
            if context.get("cancelled"):
                logger.info(f"Test run {run_id} cancelled")
                break
            
            step_number = step['step']
            step_description = step['description']
            action = step['action']
            
            # Update network monitor step
            playwright_engine.set_current_step(step_number)
            
            # Update progress
            context.set("progress", {
                "current_step": step_number,
                "total_steps": total_steps,
                "percentage": int((idx / total_steps) * 100)
            })
            
            # Create step log
            step_log = StepLog(
                run_id=run_id,
                step_number=step_number,
                step_description=step_description,
                action=action,
                status="running"
            )
            db.add(step_log)
            db.commit()
            
            try:
                # Execute step based on action type
                result = await _execute_step(
                    playwright_engine=playwright_engine,
                    step=step,
                    variables=variables,
                    context=context,
                    llm_service=llm_service
                )
                
                # Update step log with result
                step_log.status = "success"
                step_log.duration_ms = result.get('duration_ms')
                step_log.screenshot_b64 = result.get('screenshot_b64')
                step_log.target = result.get('target')
                step_log.value = result.get('value')
                step_log.details = result.get('details', {})
                db.commit()
                
            except Exception as e:
                logger.error(f"Step {step_number} failed: {e}")
                
                # Attempt self-healing before marking as failed
                from core.llm.self_healer import self_healer
                
                heal_attempt = 0
                healed = False
                heal_method = None
                
                while heal_attempt < self_healer.MAX_ATTEMPTS and not healed:
                    heal_attempt += 1
                    screenshot = await playwright_engine.get_screenshot()
                    
                    healed, heal_method, heal_result = await self_healer.attempt_heal(
                        playwright_page=playwright_engine.page,
                        step=step,
                        error=e,
                        attempt_number=heal_attempt,
                        screenshot_b64=screenshot
                    )
                    
                    if healed:
                        logger.info(f"Self-healing succeeded on attempt {heal_attempt} using: {heal_method}")
                        
                        # Update step log with healing info
                        step_log.status = "success"
                        step_log.duration_ms = result.get('duration_ms', 0)
                        step_log.screenshot_b64 = screenshot
                        step_log.details = {
                            'self_healed': True,
                            'heal_method': heal_method,
                            'heal_attempts': heal_attempt,
                            'heal_result': heal_result
                        }
                        db.commit()
                        break
                
                if not healed:
                    # Self-healing failed, mark step as failed
                    screenshot = await playwright_engine.get_screenshot()
                    
                    # Update step log
                    step_log.status = "failure"
                    step_log.error_message = str(e)
                    step_log.screenshot_b64 = screenshot
                    step_log.retry_count = heal_attempt
                    db.commit()
                
                # Generate RCA report
                network_logs = playwright_engine.get_network_logs()
                console_logs = playwright_engine.get_console_logs()
                
                rca_result = await llm_service.generate_rca_report(
                    run_id=run_id,
                    error_summary=str(e),
                    failed_step={
                        'description': step_description,
                        'action': action,
                        'target': step.get('locator_strategies', [{}])[0].get('value', ''),
                        'error': str(e)
                    },
                    screenshot_b64=screenshot,
                    network_logs=network_logs,
                    console_logs=console_logs
                )
                
                # Save RCA report
                rca_report = RCAReport(
                    run_id=run_id,
                    error_summary=str(e),
                    root_cause=rca_result.get('root_cause'),
                    affected_step=step_number,
                    network_errors={
                        'errors': [log for log in network_logs if log.get('status', 200) >= 400]
                    },
                    console_errors={
                        'errors': [log for log in console_logs if log.get('type') in ['error', 'warn']]
                    },
                    ai_explanation=rca_result.get('ai_explanation'),
                    suggested_fix=rca_result.get('suggested_fix'),
                    confidence_score=rca_result.get('confidence_score')
                )
                db.add(rca_report)
                db.commit()
                
                # Mark test run as failed
                test_run.status = "failed"
                test_run.error_summary = str(e)
                test_run.finished_at = datetime.utcnow()
                db.commit()
                
                raise
        
        # Mark test run as passed
        test_run.status = "passed"
        test_run.finished_at = datetime.utcnow()
        db.commit()
        
        return {"status": "passed", "run_id": run_id}
    
    except Exception as e:
        logger.error(f"Test run execution failed: {e}")
        
        # Update test run status
        test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
        if test_run:
            test_run.status = "failed"
            test_run.error_summary = str(e)
            test_run.finished_at = datetime.utcnow()
            db.commit()
        
        return {"status": "failed", "error": str(e)}
    
    finally:
        if playwright_engine:
            await playwright_engine.close()
        db.close()


async def _execute_step(playwright_engine, step: Dict[str, Any], 
                       variables: Dict[str, Any], context,
                       llm_service) -> Dict[str, Any]:
    """
    Execute a single step
    """
    action = step['action']
    
    # Replace variables in step values
    def replace_vars(value: str) -> str:
        if not isinstance(value, str):
            return value
        for key, val in variables.items():
            value = value.replace(f"{{{{{{key}}}}}}", str(val))
        return value
    
    # Get locator strategies
    locator_strategies = step.get('locator_strategies', [])
    
    if action == "navigate":
        url = replace_vars(locator_strategies[0].get('value', ''))
        return await playwright_engine.navigate(url)
    
    elif action == "fill_field":
        field_label = replace_vars(locator_strategies[0].get('value', ''))
        value = replace_vars(step.get('value', ''))
        return await playwright_engine.fill_field(field_label, value)
    
    elif action == "click_button":
        button_label = replace_vars(locator_strategies[0].get('name', locator_strategies[0].get('value', '')))
        return await playwright_engine.click_button(button_label)
    
    elif action == "select_dropdown":
        dropdown_label = replace_vars(locator_strategies[0].get('value', ''))
        select_value = replace_vars(step.get('select_value', ''))
        select_by = step.get('select_by', 'text')
        return await playwright_engine.select_dropdown(dropdown_label, select_value, by=select_by)
    
    elif action == "wait_for_element":
        description = step['description']
        selector = locator_strategies[0].get('value', '') if locator_strategies else None
        timeout = step.get('max_wait_ms', 30000)
        return await playwright_engine.wait_for_element(description, selector, timeout)
    
    elif action == "double_click_field":
        label = replace_vars(locator_strategies[0].get('value', ''))
        return await playwright_engine.double_click_field(label)
    
    elif action == "extract_text":
        description = step['description']
        selector = locator_strategies[0].get('value', '') if locator_strategies else None
        text = await playwright_engine.extract_text(description, selector)
        
        # Save to context if specified
        if step.get('save_to_context'):
            context.set(step['save_to_context'], text)
        
        return {
            "status": "success",
            "extracted_value": text,
            "duration_ms": 0
        }
    
    elif action == "wait":
        import asyncio
        duration_ms = step.get('duration_ms', 1000)
        await asyncio.sleep(duration_ms / 1000)
        return {"status": "success", "duration_ms": duration_ms}
    
    elif action == "db_validate":
        # TODO: Implement database validation
        return {"status": "success", "duration_ms": 0}
    
    else:
        raise ValueError(f"Unknown action: {action}")